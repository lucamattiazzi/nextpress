# Nextpress

A Python web framework inspired by Express.js, built on ASGI.

## Installation

```bash
pip install nextpress
```

## Quick Start

```python
from nextpress import Nextpress, Request, Response, Anext

app = Nextpress()

async def logger(request: Request, response: Response, anext: Anext):
    print(f"{request.method} {request.path}")
    response.set_header("X-Processed-Time", str(time.time()))
    await anext()


async def hello(response: Response[str]):
    await response.send("Hello, World!")

app.get("/", logger, hello)
```

Run with:

```bash
uvicorn example:app
```

## Features

- Express-style routing with `<method>()` and `use()`
- Route based middleware support with `anext()` pattern
- Explicit response writing
- Modular middlewares to parse input
- Route matching and chaining
- Built on uvicorn/ASGI for async performance
- Response and Request generics for typing

### Future features (feautures?)

- Pydantic validation of request and response
- CORS, multipart/form body parser, and other middlewares
- Actual tests
- Websocket handling
