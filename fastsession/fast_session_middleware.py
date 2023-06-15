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
    """

    # FastAPIのユーザーセッションを管理するためのミドルウェア。

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
        """

        # セッションID に署名してクッキーオブジェクトに保存する

        # たとえば、セッションクッキーの名前が "session" とするとき、
        # 　{"session":セッションID} な　「セッションID入り辞書オブジェクト」 を作り、
        # その　セッションID入り辞書オブジェクトに対して署名を行う
        session_id_dict_obj = {self.session_cookie_name: session_id}

        # 「セッションID入り辞書オブジェクト」 に署名をしたものは「署名済セッションID文字列」と呼ぶこととする。
        # 辞書オブジェクトがシリアライズされてるので「署名済セッションID入り辞書オブジェクト」ではなく「署名済セッションID文字列」とする。
        signed_session_id = self.serializer.encode(session_id_dict_obj)  # ser.dumps({'session_id': session_id})

        cookie = SimpleCookie()

        # クッキーオブジェクトにキーを "session" として、今署名済の　「署名済セッションID文字列」　を格納する
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
        """

        # リクエストをディスパッチし、セッション管理を行う。
        # クライアントからのリクエストに含まれるクッキーから
        # 「署名済セッションID文字列」を取得する
        signed_session_id = request.cookies.get(self.session_cookie_name)

        cookie = None

        if signed_session_id is None:
            # セッションクッキーが無い完全新規アクセス
            # => セッションの新規生成
            self.logi(f"Completely new access with no session cookies")

            # セッションID に署名してクッキーオブジェクトに保存する。
            # また request.state 以下にセッションマネージャをぶるさげてセッションの入出力ができるようにする
            cookie = await self.create_new_session_id_and_store(request, cause="new")

        else:
            # セッションクッキーがある状態でアクセス

            # 「署名済セッションID文字列」をデコードして「セッションID入り辞書オブジェクト」を得る
            decoded_dict, err = self.serializer.decode(signed_session_id)

            if decoded_dict is not None:

                # - クッキー署名検証に成功したとき

                # 「セッションID入り辞書オブジェクト」から セッションID を取得する
                session_id = decoded_dict.get(self.session_cookie_name)
                session_store = self.session_store.get_store(session_id)

                if session_store is None:
                    # 正しい署名のクッキーがあり、そこからデコードしたセッションIDも正常
                    # だがセッションIDにひもづいたセッションストアが正しく取得できなかった
                    # こうなる原因はサーバーを再起動しオンメモリのストアが消えたがユーザーの
                    # ブラウザにセッションクッキーが残っている場合
                    # => セッションIDを再生成し、ストアを再生成する

                    self.logi(f"Session cookies available. No store.")
                    cookie = await self.create_new_session_id_and_store(request, cause="valid_cookie_but_no_store")
                    # request.state.session["__cause__"] =
                else:

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
                # クッキーの署名検証に失敗
                # 理由１　セッションidの改ざん
                # 理由２　有効期限切れ
                # => 旧セッションID用のストレージを削除する
                # => 新たにセッションを生成
                self.logi(f"Session cookies available. Verification failed! err:{err}")

                if err == "SignatureExpired":
                    # セッションの有効期限が切れていた場合
                    pass

                cookie = await self.create_new_session_id_and_store(request, cause=f"renew after {err}")

        response = await call_next(request)

        # ここから response 側の処理
        if cookie is not None:
            # - セットすべきクッキーがあるとき
            # => session_id をエンコードしたクッキーをセットする

            cookie_val = cookie.output(header="").strip()
            response.headers["Set-Cookie"] = cookie_val  # レスポンスヘッダにセッションID署名済データが入ったクッキーをセットし、クライアント側に反映する

        return response

    async def create_new_session_id_and_store(self, request, cause=None):
        """
        Create a new session ID and its corresponding store.
        """

        # セッションID に署名してクッキーオブジェクトに保存する。また request.state 以下にセッションマネージャをぶるさげてセッションの入出力ができるようにする
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
