# FastSessionMiddleware

[English](https://github.com/riversun/FastSession/blob/main/README.md) | [&#26085;&#26412;&#35486;](https://github.com/riversun/FastSession/blob/main/README_ja.md)


FastSessionMiddlewareは、FastAPIアプリケーションでユーザーセッションを管理するためのミドルウェアです。

# インストール

```
pip install fastsession
```


- **セッションデータをクッキーに保存しない**: FastSessionMiddlewareは、セッションデータをクッキーに直接保存しません。代わりに、クッキーにはセッションIDが含まれています。セッションデータはサーバー側のストア（デフォルトでは`MemoryStore()`）に保存されます。このアプローチにより、セッションデータの安全性が向上し、クッキーのサイズ制限に制約されることがありません。

この特徴により、セッションデータの漏洩や改ざんのリスクが低くなります。また、クッキーのサイズ制限に制約されることなく、大量のセッションデータを安全に管理できます。

## 使用方法

以下の手順に従って、FastSessionMiddlewareを使用できます。

1. `FastSessionMiddleware`クラスをインポートします。
2. `store`として使用するセッションの保存先を指定します。デフォルトでは`MemoryStore`が使用されますが、独自のストアを実装することもできます。
3. `secret_key`を指定します。これはクッキー署名に使用されます。
4. 必要に応じて、`http_only`、`secure`、`max_age`などのオプションを設定します。
5. FastAPIアプリケーションを作成し、`FastSessionMiddleware`をミドルウェアとして追加します。

以下に、FastAPIアプリケーションでFastSessionMiddlewareを使用する例を示します。

```python
from fastapi import FastAPI
from fastsession import FastSessionMiddleware,MemoryStore

app = FastAPI()

# カスタムのセッションストアを作成する場合は、MemoryStoreを継承して実装します
class CustomSessionStore(MemoryStore):
    pass

# FastSessionMiddlewareの設定
app.add_middleware(
    FastSessionMiddleware,
    secret_key="your_secret_key",
    store=CustomSessionStore(),
    http_only=True,
    secure=True,
    max_age=3600,
    session_cookie="sid",
    session_object="session"
)

# ルートハンドラ
@app.get("/")
async def root(session: FastSession):
    # セッションの操作を行うことができます
    session["counter"] = session.get("counter", 0) + 1
    return {"message": "Hello, FastAPI!"}
```

## クラスとメソッドの詳細

### クラス: FastSession

`FastSession`クラスは、セッションの操作を行うためのクラスです。

#### `get_session()`

セッションストアを取得します。

#### `clear_session()`

セッションをクリアします。

#### `get_session_id()`

セッションIDを取得します。

#### `save_session()`

セッションを保存します。

### クラス: FastSessionMiddleware

`FastSessionMiddleware`クラスは、FastAPIアプリケーションでユーザーセッションを管理するためのミドルウェアです。

#### メソッド: `__init__()`

ミドルウェアの初期化を行います。以下のパラメータを受け取ります。

- `app`: FastAPIアプリケーションのインスタンス
- `secret_key`: クッキー署名に使用する秘密

キー
- `store`: セッションの保存先を指定するストアオブジェクト。デフォルトは`MemoryStore()`
- `http_only`: クッキーがJavaScriptなどのクライアントサイドのスクリプトからアクセス不可かどうかを指定します。デフォルトは`True`
- `secure`: HTTPSが必要かどうかを指定します。デフォルトは`True`
- `max_age`: セッションの有効期間を秒単位で指定します。デフォルトは`0`で、ブラウザを起動している間のみ有効です。
- `session_cookie`: セッションクッキーの名前を指定します。デフォルトは`"sid"`
- `session_object`: セッションオブジェクトをリクエストの`state`以下に保存する際の属性名を指定します。デフォルトは`"session"`
- `skip_session_header`: 特定のヘッダと値のペアが含まれている場合にセッション管理をスキップするためのオプションです。デフォルトは`None`
- `logger`: ロガーオブジェクトを指定します。デフォルトは標準出力にログを出力するロガー


## セッション処理を明示的にスキップする方法


```python
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastsession import FastSessionMiddleware,MemoryStore

app = FastAPI()

# FastSessionMiddlewareの設定
app.add_middleware(
    FastSessionMiddleware,
    secret_key="your_secret_key",
    skip_session_header={"header_name": "X-FastSession-Skip", "header_value": "skip"}
)

# ルートハンドラ
@app.get("/")
async def root(request: Request):
    # 特定のヘッダと値が含まれている場合にセッション管理をスキップする
    if "X-FastSession-Skip" in request.headers and request.headers["X-FastSession-Skip"] == "skip":
        return JSONResponse({"message": "Session management skipped."})

    # セッションの操作を行うことができます
    session = request.state.session
    session["counter"] = session.get("counter", 0) + 1
    return JSONResponse({"message": "Session managed.", "counter": session["counter"]})
```

上記の例では、`X-FastSession-Skip`という名前のヘッダがリクエストに含まれ、その値が`skip`である場合にセッション管理がスキップされます。それ以外の場合はセッション管理が行われ、セッションのカウンタが増加します。


このように、`skip_session_header`オプションを使用することで、特定のヘッダと値のペアをチェックしてセッション管理のスキップを制御することができます。


# カスタムストアの作成

FastSessionMiddlewareで使用するカスタムセッションストアを作成するには、次の手順に従います。

`MemoryStore`の実装を参考に、カスタムストアクラスを作成します。

以下に、カスタムストアの作成手順を示します。

```python
import time

class CustomStore:
    def __init__(self):
        """
        カスタムストアのインスタンスを初期化します。セッションデータを格納するための辞書を作成します。
        """
        self.session_data = {}

    def has_session_id(self, session_id):
        """
        セッションIDがストア内に存在するかを確認します。

        :param session_id: 確認するセッションID
        :return: セッションIDが存在する場合はTrue、存在しない場合はFalseを返します
        """
        return session_id in self.session_data

    def create_store(self, session_id):
        """
        新しいセッションIDに対応するストアを作成します。

        :param session_id: ストアを作成するためのセッションID
        :return: 新しく作成されたストア
        """
        self.session_data[session_id] = {
            "created_at": int(time.time()),
            "store": {}
        }
        return self.session_data[session_id]["store"]

    def get_store(self, session_id):
        """
        セッションIDに対応するストアを取得します。

        :param session_id: 取得するストアのセッションID
        :return: セッションIDに対応するストア、存在しない場合はNoneを返します
        """
        session_info = self.session_data.get(session_id)
        if session_info:
            return session_info["store"]
        else:
            return None

    def save_store(self, session_id):
        """
        セッションIDに対応するストアを永続化します。

        :param session_id: 永続化するストアのセッションID
        """
        # カスタムの永続化処理を実装する
        pass

    def gc(self):
        """
        古いセッションデータをクリーンアップします。カスタムのクリーンアップ処理を実装する場合にのみオーバーライドします。
        """
        current_time = int(time.time())
        sessions_to_delete = []
        for session_id, session_info in self.session_data.items():
            if current_time - session_info["created_at"] > 3600 * 24:
                sessions_to_delete.append(session_id)

        for session_id in sessions_to_delete:
            del self.session_data[session_id]

```

上記の例では、`CustomStore`クラスを作成し、必要なメソッドを実装しています。また、`cleanup_old_sessions()`メソッドをオーバーライドして、24時間以上経過したセッションデータを削除するカスタムのクリーンアップ処理を実装しています。

このようにして、カスタムセッションストアを作成し、FastSessionMiddlewareの`store`パラメータに指定することで使用することができます。

```python
from fastapi import FastAPI


from fastsession import FastSessionMiddleware,MemoryStore

app = FastAPI()

custom_store = CustomStore()

app.add_middleware(
    FastSessionMiddleware,
    secret_key="your_secret_key",
    store=custom_store()
)

# アプリケーションのロジックを追加する
```

上記の例では、FastAPIアプリケーションでカスタムストアを使用する方法を示しています。`FastSessionMiddleware`の`store`パラメータに、作成したカスタムストアオブジェクトを指定します。

これにより、カスタムストアを使用してセッションデータを管理することができます。