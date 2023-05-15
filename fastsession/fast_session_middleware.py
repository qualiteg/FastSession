import uuid
from http.cookies import SimpleCookie

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from .memory_store import MemoryStore
from .timed_signature_serializer import TimedSignatureSerializer


class FastSession:
    def __init__(self, store, session_id, session_save):
        self.session_store = store
        self.session_id = session_id
        self.session_save = session_save

    def get_session(self):
        return self.session_store

    def clear_session(self):
        self.session_store.clear()

    def get_session_id(self):
        return self.session_id

    def save_session(self):
        self.session_save()
        pass


class FastSessionMiddleware(BaseHTTPMiddleware):
    """
    A FastAPI middleware for managing user sessions.
    FastAPIのユーザーセッションを管理するためのミドルウェア。
    """

    def __init__(self, app,
                 secret_key,  # クッキー署名用のキー
                 store=MemoryStore,  # セッション保存用ストア
                 http_only=True,  # True: CookieがJavaScriptなどのクライアントサイドのスクリプトからアクセス不可となる
                 secure=True,  # True: Https が必要
                 max_age=0,  # 0を指定すると、ブラウザを起動しているときのみ有効。0より大きな値を指定するとブラウザを閉じても有効時間内はセッションが継続される
                 session_cookie="sid",  # セッションクッキーの名前
                 session_object="session",  # request.state以下にぶるさげるSessionオブジェクトの属性名
                 logger=None):
        """
        Initialize FastSessionMiddleware.
        FastSessionMiddlewareを初期化する。
        """
        super().__init__(app)

        self.http_only = http_only
        self.max_age = max_age
        self.secure = secure
        self.secret_key = secret_key
        self.session_cookie_name = session_cookie
        self.session_store = store
        self.serializer = TimedSignatureSerializer(self.secret_key, expired_in=self.max_age)
        self.session_object = session_object
        self.logger = logger

    def logi(self, message: str):
        if self.logger is not None:
            self.logger.info(message)

    def create_session_cookie(self, session_id):
        """
        Create and sign a session cookie.
        セッションキーを署名してクッキーに保存。
        """
        session_id_dict_obj = {self.session_cookie_name: session_id}
        signed_session_id = self.serializer.encode(session_id_dict_obj)  # ser.dumps({'session_id': session_id})

        cookie = SimpleCookie()
        cookie[self.session_cookie_name] = signed_session_id

        if self.http_only:
            cookie[self.session_cookie_name]["httponly"] = True  # Set the HTTP-only flag. HTTP-onlyフラグを設定

        if self.secure:
            cookie[self.session_cookie_name]["secure"] = True  # Set the Secure flag. Secure フラグを設定

        if self.max_age > 0:
            cookie[self.session_cookie_name][
                "max-age"] = self.max_age  # Set the Max-Age attribute. Max-Age 属性を設定（この例では1時間）
            # cookie[self.session_cookie_name]["max-age"] = 60 * 60 * 24 * 365 * 100  # 100 years for example

        return cookie

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Dispatch the request, handling session management.
        リクエストをディスパッチし、セッション管理を行う。
        """

        # Get session key from cookies. クッキーからセッションキーを取得
        signed_session_id = request.cookies.get(self.session_cookie_name)

        cookie = None
        if signed_session_id is None:
            # No session cookie, completely new access.
            # => Generate a new session.
            # セッションクッキーが無い完全新規アクセス
            # => セッションの新規生成
            self.logi(f"Completely new access with no session cookies")
            cookie = await self.create_new_session_id_and_store(request, cause="new")

        else:
            # Access with session cookie. セッションクッキーがある状態でアクセス
            decoded_dict, err = self.serializer.decode(signed_session_id)

            if decoded_dict is not None:
                #
                # Cookie signature verification succeeded.
                # クッキー署名検証に成功
                session_id = decoded_dict.get(self.session_cookie_name)
                session_store = self.session_store.get_store(session_id)

                if session_store is None:
                    # The session cookie is correct and the session ID decoded from it is also normal.
                    # However, the session store linked to the session ID could not be properly retrieved.
                    # This happens when the server is restarted and the in-memory store is lost,
                    # but the session cookie remains in the user's browser.
                    # => Regenerate the session ID and the store.

                    # 正しい署名のクッキーがあり、そこからデコードしたセッションIDも正常
                    # だがセッションIDにひもづいたセッションストアが正しく取得できなかった
                    # こうなる原因はサーバーを再起動しオンメモリのストアが消えたがユーザーの
                    # ブラウザにセッションクッキーが残っている場合
                    # => セッションIDを再生成し、ストアを再生成する

                    self.logi(f"Session cookies available. No store.")
                    cookie = await self.create_new_session_id_and_store(request, cause="valid_cookie_but_no_store")
                    # request.state.session["__cause__"] =
                else:
                    # The session cookie is correct, the session ID decoded from it is also normal,
                    # and the session store linked to the session ID was properly retrieved.

                    # 正しい署名のクッキーがあり、そこからデコードしたセッションIDも正常
                    # かつセッションIDにひもづいたセッションストアが正しく取得できた
                    self.logi(f"Session cookies,Store available.")

                    setattr(request.state,
                            self.session_object,
                            FastSession(
                                store=session_store,
                                session_id=session_id,
                                session_save=lambda: self.session_store.save_store(session_id))
                            )

                    # request.state.session_save = lambda: self.session_store.save_store(session_id)
                    session_store["__cause__"] = "success"

            else:
                # Cookie signature verification failed.
                # Signature verification of the session id failed due to some reason.
                # Reason 1: Tampering with the session id.
                # Reason 2: Expired.
                # => Delete the storage for the old session ID.
                # => Generate a new session.

                # クッキーの署名検証に失敗
                # 理由１　セッションidの改ざん
                # 理由２　有効期限切れ
                # => 旧セッションID用のストレージを削除する
                # => 新たにセッションを生成
                self.logi(f"Session cookies available. Verification failed! err:{err}")

                if err == "SignatureExpired":
                    # In case the session has expired.
                    # セッションの有効期限が
                    # Expired. セッションの有効期限が切れていた場合
                    pass

                cookie = await self.create_new_session_id_and_store(request, cause=f"renew after {err}")

        response = await call_next(request)

        # From here, processing for the response side.
        # ここから response 側の処理
        if cookie is not None:
            # If there is a cookie to be set.
            # => Set a cookie that encodes the session_id.

            # セットすべきクッキーがある場合
            # => session_id をエンコードしたクッキーをセットする
            cookie_val = cookie.output(header="").strip()
            response.headers["Set-Cookie"] = cookie_val

        return response

    async def create_new_session_id_and_store(self, request, cause=None):
        """
        Create a new session ID and its corresponding store.
        新しいセッションIDとそのストアを生成する。
        """
        session_id = str(uuid.uuid4())
        session_store = self.session_store.create_store(session_id)

        if cause is not None:
            session_store["__cause__"] = cause  # セッションが新規生成された理由を格納

        fast_session_obj = FastSession(
            store=session_store,
            session_id=session_id,
            session_save=lambda: self.session_store.save_store(session_id)
        )

        # request.state に self.session_object に指定された属性名で FastSessionオブジェクトをぶらさげる
        setattr(request.state,
                self.session_object,
                fast_session_obj)

        self.session_store.gc()  # たまったストアのクリーンアップをトライする

        cookie = self.create_session_cookie(session_id)
        return cookie
