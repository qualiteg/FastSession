import pytest
from unittest.mock import Mock

from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from fastsession.fast_session_middleware import FastSessionMiddleware, MemoryStore
from starlette.requests import Request
from starlette.responses import Response


def test_create_session_id_and_store():
    """
    Test session ID creation and store operation.

    テストセッションIDの作成とストア操作
    """

    async def test_route(request):
        return PlainTextResponse("Hello, world!")

        # ルートをリストに格納

    routes = [
        Route("/", endpoint=test_route)
    ]
    # アプリケーションの作成とミドルウェアの追加
    app = Starlette(routes=routes)

    app.add_middleware(FastSessionMiddleware,
                       secret_key='test-secret',
                       store=MemoryStore(),
                       http_only=True,
                       max_age=3600,
                       secure=True,
                       session_cookie="sid"
                       )
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "Hello, world!"
    assert "sid" in response.cookies  # sid クッキーを検証


def test_session_counter_increment():
    """
    Test that the session variable 'test_counter' is incremented with each API access.

    セッション変数'test_counter'がAPIアクセスごとにインクリメントされることをテスト
    """

    async def test_route(request):
        session = request.state.session.get_session()
        if "test_counter" not in session:
            session["test_counter"] = 0

        session["test_counter"] += 1

        return PlainTextResponse(f"Counter: {session['test_counter']}")

    # ルートをリストに格納
    routes = [
        Route("/", endpoint=test_route)
    ]

    # アプリケーションの作成とミドルウェアの追加
    app = Starlette(routes=routes)
    is_cookie_secure = False  # テスト用途なので False にする
    app.add_middleware(FastSessionMiddleware,
                       secret_key='test-secret',
                       store=MemoryStore(),  # Use the same memory store
                       http_only=True,
                       max_age=3600,
                       secure=is_cookie_secure,
                       session_cookie="sid"
                       )
    client = TestClient(app)

    # First request
    response = client.get("/")
    assert response.status_code == 200
    assert "Counter: 1" in response.text

    # Second request
    response = client.get("/")
    assert response.status_code == 200
    assert "Counter: 2" in response.text

    # Third request
    response = client.get("/")
    assert response.status_code == 200
    assert "Counter: 3" in response.text


import time


def test_session_cookie_expiry():
    """
    Test that the session cookie expires after the max_age limit (1 second in this case).

    セッションクッキーがmax_age（この場合は1秒）の制限後に期限切れになることをテストします。
    """

    async def test_route(request):
        session = request.state.session.get_session()

        if "test_counter" not in session:
            session["test_counter"] = 0

        session["test_counter"] += 1

        return PlainTextResponse(f"Counter: {session['test_counter']}")

    # ルートをリストに格納
    routes = [
        Route("/", endpoint=test_route)
    ]

    # アプリケーションの作成とミドルウェアの追加
    app = Starlette(routes=routes)
    is_cookie_secure = False  # テスト用途なので False にする
    app.add_middleware(FastSessionMiddleware,
                       secret_key='test-secret',
                       store=MemoryStore(),  # Use the same memory store
                       http_only=True,
                       max_age=1,  # Set max_age to 1 second
                       secure=is_cookie_secure,
                       session_cookie="sid"
                       )
    client = TestClient(app)

    # First request
    response = client.get("/")
    assert response.status_code == 200
    assert "Counter: 1" in response.text

    # Wait for more than max_age seconds
    time.sleep(2)

    # Second request after expiry
    response = client.get("/")
    assert response.status_code == 200
    assert "Counter: 1" in response.text  # Counter should reset to 1


def test_session_cookie_not_persisted_with_secure_option():
    """
    Test that the session cookie is not persisted when the 'secure' option is True.

    'secure'オプションがTrueの場合、セッションクッキーが維持されないことをテスト
    """

    app = Starlette()
    is_cookie_secure = True  # セキュリティ設定を有効にする
    app.add_middleware(FastSessionMiddleware,
                       secret_key='test-secret',
                       store=MemoryStore(),  # Use the same memory store
                       http_only=True,
                       max_age=3600,
                       secure=is_cookie_secure,
                       session_cookie="sid"
                       )

    @app.route("/")
    async def test_route(request):
        session = request.state.session.get_session()
        if "test_counter" not in session:
            session["test_counter"] = 0

        session["test_counter"] += 1

        return PlainTextResponse(f"Counter: {session['test_counter']}")

    client = TestClient(app)

    # First request
    response = client.get("/")
    assert response.status_code == 200
    assert "Counter: 1" in response.text

    # Second request
    response = client.get("/")
    assert response.status_code == 200
    # Since the secure option is set, the cookie should not be persisted
    # and the counter should not increment.
    assert "Counter: 1" in response.text


def test_check_httponly_flag_in_cookie():
    # テストルートの定義
    async def test_route(request):
        session = request.state.session.get_session()
        if "test_counter" not in session:
            session["test_counter"] = 0

        session["test_counter"] += 1

        return PlainTextResponse(f"Counter: {session['test_counter']}")

    # アプリケーションの作成とミドルウェアの追加
    app = Starlette()
    app.add_route("/", test_route)

    is_cookie_secure = False  # テスト用途なので False にする
    is_http_only = True  # HttpOnly を付与する
    app.add_middleware(FastSessionMiddleware,
                       secret_key='test-secret',
                       store=MemoryStore(),  # Use the same memory store
                       http_only=is_http_only,
                       max_age=3600,
                       secure=is_cookie_secure,
                       session_cookie="sid"
                       )

    # テストクライアントの作成
    client = TestClient(app)

    # First request
    response = client.get("/")
    assert 'HttpOnly' in response.headers['Set-Cookie']


def test_check_no_httponly_flag_in_cookie():
    """
    Test that the HttpOnly flag is not set in the cookie when http_only is False.

    http_onlyがFalseの場合、クッキーにHttpOnlyフラグが設定されていないことをテストします。
    """

    # テストルートの定義
    async def test_route(request):
        session = request.state.session.get_session()
        if "test_counter" not in session:
            session["test_counter"] = 0

        session["test_counter"] += 1

        return PlainTextResponse(f"Counter: {session['test_counter']}")

    # アプリケーションの作成とミドルウェアの追加
    app = Starlette()
    app.add_route("/", test_route)

    is_cookie_secure = False  # テスト用途なので False にする
    is_http_only = False  # HttpOnly を付与しない
    app.add_middleware(FastSessionMiddleware,
                       secret_key='test-secret',
                       store=MemoryStore(),  # Use the same memory store
                       http_only=is_http_only,
                       max_age=3600,
                       secure=is_cookie_secure,
                       session_cookie="sid"
                       )

    # テストクライアントの作成
    client = TestClient(app)

    # First request
    response = client.get("/")
    assert 'HttpOnly' not in response.headers['Set-Cookie']

@pytest.mark.asyncio
async def test_dispatch_should_skip_session_management_with_skip_header():
    app = Mock(return_value=Response("OK"))  # モックのASGIアプリケーションを作成します
    middleware = FastSessionMiddleware(
        app=app,
        secret_key="test",
        skip_session_header={"header_name": "X-FastSession-Skip", "header_value": "skip"}
    )

    # Starlette の Request オブジェクトを(UTなどの目的で)自前で生成するときは、
    # (1) ヘッダーを　小文字にした、タプルで指定する
    # (2) バイト文字列（b""） で指定する
    headers = [(b"x-fastsession-skip", b"skip")]
    request = Request(scope={"type": "http", "headers": headers}, receive=None)

    # headers = [(b"X-FastSession-Skip", b"skip")]
    # request = Request(scope={"type": "http", "headers": headers}, receive=None)

    class MockResponse:
        def __init__(self):
            self.headers = {}

    emulated_response=MockResponse()

    async def call_next(request):
        return emulated_response

    response = await middleware.dispatch(request,call_next)
    print(f"res:{response}")
    assert not hasattr(request.state, 'session')  # request.stateにsession属性が存在しないことを確認します


@pytest.mark.asyncio
async def test_dispatch_should_not_skip_session_management_without_skip_heade1r():
    # スキップヘッダが存在しないとき、appが直接呼び出されないことを確認します
    app = Mock(return_value=Response("OK"))  # モックのASGIアプリケーションを作成します
    middleware = FastSessionMiddleware(
        app=app,
        secret_key="test",
        skip_session_header={"header_name": "X-FastSession-Skip", "header_value": "skip"}
    )

    headers = [(b"ignore", b"ignore")]
    request = Request(scope={"type": "http", "headers": headers}, receive=None)

    # headers = [(b"X-FastSession-Skip", b"skip")]
    # request = Request(scope={"type": "http", "headers": headers}, receive=None)

    class MockResponse:
        def __init__(self):
            self.headers = {}

    emulated_response = MockResponse()

    async def call_next(request):
        return emulated_response

    response = await middleware.dispatch(request, call_next)
    print(f"res:{response}")
    assert hasattr(request.state, 'session')  # request.stateにsession属性が存在することを確認します
