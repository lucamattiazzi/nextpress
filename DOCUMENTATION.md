# Nextpress Documentation

**Nextpress** is a Python web framework inspired by Express.js, built on ASGI. It provides an intuitive, Express-style API with middleware chaining, typed request/response handling, and full async support.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [API Reference](./docs/API_REFERENCE.md)
- [Middlewares](./docs/MIDDLEWARES.md)
- [Advanced Usage](./docs/ADVANCED_USAGE.md)

## Installation

Install Nextpress using pip:

```bash
pip install nextpress
```

Or with uv:

```bash
uv add nextpress
```

### Requirements

- Python >= 3.13
- pydantic >= 2.11.9

### Development Dependencies

For development and running the server:

```bash
uv add --dev uvicorn watchfiles
```

## Quick Start

Create a simple web server with Nextpress:

```python
from nextpress import Nextpress, Request, Response

app = Nextpress()

async def hello(response: Response[str]):
    await response.send_text("Hello, World!")

app.get("/", hello)
```

Run the server:

```bash
uvicorn your_module:app
```

Or with auto-reload for development:

```bash
uvicorn your_module:app --reload
```

## Core Concepts

### 1. Application Instance

Create a Nextpress application:

```python
from nextpress import Nextpress

app = Nextpress()
```

The `app` instance is an ASGI application that can be served by any ASGI server (uvicorn, hypercorn, daphne, etc.).

### 2. Routing

Define routes using HTTP method helpers:

```python
app.get("/users", handler)           # GET requests
app.post("/users", handler)          # POST requests
app.put("/users/:id", handler)       # PUT requests
app.patch("/users/:id", handler)     # PATCH requests
app.delete("/users/:id", handler)    # DELETE requests
app.options("/users", handler)       # OPTIONS requests
app.use("/api", middleware)          # All methods
```

### 3. Handlers and Middleware

Handlers are async functions that process requests. They can receive `Request`, `Response`, and `Anext` parameters:

```python
async def handler(request: Request, response: Response):
    # Process request and send response
    await response.send_json({"status": "ok"})
```

Middleware uses the `anext` parameter to chain execution:

```python
async def logger(request: Request, response: Response, anext: Anext):
    print(f"{request.method} {request.path}")
    await anext()  # Continue to next middleware/handler
```

### 4. Request Object

The `Request` object provides access to incoming request data:

```python
async def handler(request: Request):
    method = request.method           # HTTP method
    path = request.path              # Request path
    query = request.query_params     # Query parameters
    body = request.body              # Parsed body (if middleware added it)
```

#### Type-Safe Request Bodies

Use generics to type request bodies:

```python
from typing import TypedDict

class UserData(TypedDict):
    name: str
    email: str

async def create_user(request: Request[UserData]):
    name = request.body["name"]      # Type-safe access
    email = request.body["email"]
```

### 5. Response Object

The `Response` object provides methods to send data:

```python
async def handler(response: Response):
    # Send plain text
    await response.send_text("Hello")

    # Send JSON
    await response.send_json({"message": "Hello"})

    # Send bytes
    await response.send_bytes(b"binary data")

    # Set headers
    response.set_header("X-Custom", "value")

    # Set status code
    response.set_status_code(201)
```

#### Type-Safe Response Bodies

Use generics to type response bodies:

```python
class ApiResponse(TypedDict):
    message: str
    status: int

async def handler(response: Response[ApiResponse]):
    # Type checkers know this is correct
    await response.send_json({
        "message": "Success",
        "status": 200
    })
```

### 6. Middleware Chaining

Chain multiple handlers/middlewares on a single route:

```python
app.get("/api/users", auth_middleware, logger, get_users)
```

Execution flows through each function in order. Each middleware must call `await anext()` to continue:

```python
async def auth(request: Request, response: Response, anext: Anext):
    token = request.query_params.get("token")
    if not token:
        response.set_status_code(401)
        await response.send_json({"error": "Unauthorized"})
        return  # Stop execution

    await anext()  # Continue to next handler
```

### 7. Dependency Injection

Handlers only receive the parameters they need. Use type hints to specify dependencies:

```python
# Only needs response
async def simple(response: Response):
    await response.send_text("Simple!")

# Needs both request and response
async def complex(request: Request, response: Response):
    data = request.query_params.get("data")
    await response.send_json({"data": data})

# Middleware needs anext
async def middleware(request: Request, response: Response, anext: Anext):
    # Do something
    await anext()
```

## Examples

### Basic API Server

```python
from nextpress import Nextpress, Request, Response
from nextpress.middlewares import json_body_parser

app = Nextpress()

async def get_items(response: Response):
    items = [{"id": 1, "name": "Item 1"}]
    await response.send_json({"items": items})

async def create_item(request: Request, response: Response):
    item = request.body
    response.set_status_code(201)
    await response.send_json({"item": item})

app.get("/items", get_items)
app.post("/items", json_body_parser, create_item)
```

### With Typed Request/Response

```python
from typing import TypedDict
from nextpress import Nextpress, Request, Response
from nextpress.middlewares import json_body_parser

app = Nextpress()

class CreateUserRequest(TypedDict):
    name: str
    email: str

class UserResponse(TypedDict):
    id: int
    name: str
    email: str

async def create_user(
    request: Request[CreateUserRequest],
    response: Response[UserResponse]
):
    # Type-safe access
    user_data = request.body

    # Create user (simplified)
    user = {
        "id": 1,
        "name": user_data["name"],
        "email": user_data["email"]
    }

    response.set_status_code(201)
    await response.send_json(user)

app.post("/users", json_body_parser, create_user)
```

### Global Middleware

```python
from nextpress import Nextpress, Request, Response, Anext

app = Nextpress()

async def logger(request: Request, response: Response, anext: Anext):
    print(f"{request.method} {request.path}")
    await anext()

# Apply to all routes
app.use("/*", logger)

async def hello(response: Response):
    await response.send_text("Hello!")

app.get("/", hello)
```

## Running the Application

### With uvicorn

```bash
# Production
uvicorn your_module:app --host 0.0.0.0 --port 8000

# Development with auto-reload
uvicorn your_module:app --reload
```

### With other ASGI servers

Nextpress is ASGI-compatible and works with any ASGI server:

```bash
# Hypercorn
hypercorn your_module:app

# Daphne
daphne your_module:app
```

## Next Steps

- **[API Reference](./docs/API_REFERENCE.md)** - Complete API documentation
- **[Middlewares](./docs/MIDDLEWARES.md)** - Built-in and custom middlewares
- **[Advanced Usage](./docs/ADVANCED_USAGE.md)** - Streaming, error handling, and more

## Architecture

Nextpress is built on:

- **ASGI**: Standard Python async web server interface
- **Pydantic**: Data validation and type safety
- **Python 3.13+**: Modern Python with type hints and async/await

The framework follows Express.js patterns while leveraging Python's type system for better developer experience and runtime safety.
