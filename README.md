# Nextpress

A Python web framework inspired by Express.js, built on ASGI.

## Installation

```bash
pip install nextpress
```

## Quick Start

```python
from nextpress import Nextpress
import time

app = Nextpress()

async def logger(request, response, next):
    print(f"{request.method} {request.path}")
    response.set_header("X-Processed-Time", str(time.time()))


async def hello(request, response, next):
    await response.send("Hello, World!")

app.get("/", logger, hello)
```

Run with:

```bash
uvicorn example:app
```

## Features

- Express-style routing with `<method>()`, `post()`, and `use()`
- Route based middleware support with `next()` pattern
- JSON responses via `response.json()`
- Route matching and chaining
- Built on uvicorn/ASGI for async performance
