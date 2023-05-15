# FastSession

FastSession is a session management library for FastAPI. 

It provides a middleware, `FastSessionMiddleware`, 
that helps you manage user sessions effectively in your FastAPI applications.

## Features

Only the session ID is stored as a browser cookie.
(Similar to Java Servlet and Node.js express session)

The session ID can be shared only through signed and confidential 
communication channels, and since no session contents are stored 
in the browser, an extremely secure session system can be built.

- Session ID generation and session data storage.
- Session cookie management with signature verification for enhanced security.
- In-memory store for session data enabled.

## Installation

Use the package manager PIP to install FastSession.

```
pip install fastsession
```

## Usage

Here is a basic usage example:

```python
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from fastsession import FastSessionMiddleware, MemoryStore

HOST = 'localhost'
PORT = 18080

app = FastAPI()
app.add_middleware(FastSessionMiddleware,
                   secret_key="my-secret-key",  # Key for cookie signature
                   store=MemoryStore(),  # Store for session saving
                   http_only=True,  # True: Cookie cannot be accessed from client-side scripts such as JavaScript
                   secure=False,  # True: Requires Https
                   max_age=0,
                   # When 0 is specified, it is only effective while the browser is active. If a value greater than 0 is specified, the session will continue for the specified time even after closing the browser
                   session_cookie="sid",  # Name of the session cookie
                   session_object="session"  # Attribute name of the Session manager under request.state
                   )


@app.get("/session_test")
async def session_test(request: Request):
    # get session manager
    session_mgr = request.state.session

    # get session store (dictionary)
    session = session_mgr.get_session()

    # get session id
    session_id = session_mgr.get_session_id()
    
    print(f"sessionID:{session_id}")

    if "test_counter" not in session:
        session["test_counter"] = 0

    session["test_counter"] += 1

    return {"test_counter": session['test_counter']}


app.mount("/", StaticFiles(directory="html", html=True), name="public")


def start_server():
    uvicorn.run(app, host=HOST, port=PORT)


def main():
    start_server()


if __name__ == "__main__":
    main()

````