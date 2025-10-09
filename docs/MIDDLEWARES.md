# Middlewares

Middlewares are functions that intercept requests and can modify the request, response, or control the flow of execution.

## Table of Contents

- [Understanding Middleware](#understanding-middleware)
- [Built-in Middlewares](#built-in-middlewares)
- [Creating Custom Middleware](#creating-custom-middleware)
- [Middleware Patterns](#middleware-patterns)

## Understanding Middleware

Middleware functions in Nextpress follow the Express.js pattern. They:

1. Receive `Request`, `Response`, and/or `Anext` parameters
2. Can modify the request or response
3. Call `await anext()` to pass control to the next handler
4. Can short-circuit the chain by sending a response without calling `anext()`

### Basic Structure

```python
from nextpress import Request, Response, Anext

async def my_middleware(request: Request, response: Response, anext: Anext):
    # Code before next handler
    print(f"Request: {request.method} {request.path}")

    # Continue to next handler
    await anext()

    # Code after next handler
    print("Response sent")
```

### Execution Order

Handlers execute in the order they're registered:

```python
app.get("/", middleware1, middleware2, handler)
```

1. `middleware1` runs
2. `middleware1` calls `await anext()`
3. `middleware2` runs
4. `middleware2` calls `await anext()`
5. `handler` runs and sends response
6. Control returns to `middleware2` (after `await anext()`)
7. Control returns to `middleware1` (after `await anext()`)

## Built-in Middlewares

Nextpress provides several built-in middlewares in `nextpress.middlewares`.

### `json_body_parser`

Parses JSON request bodies and adds them to `request.body`.

**Usage:**
```python
from nextpress import Nextpress, Request, Response
from nextpress.middlewares import json_body_parser

app = Nextpress()

async def create_user(request: Request):
    data = request.body  # Parsed JSON as dict
    name = data.get("name")
    # Process data...

app.post("/users", json_body_parser, create_user)
```

**Features:**
- Only processes POST, PUT, and PATCH requests
- Skips if no body is present
- Returns 400 error for invalid JSON
- Sets `request.body` to the parsed dictionary

**Type-Safe Usage:**
```python
from typing import TypedDict

class CreateUserData(TypedDict):
    name: str
    email: str

async def create_user(request: Request[CreateUserData]):
    name = request.body["name"]  # Type-safe access
    email = request.body["email"]

app.post("/users", json_body_parser, create_user)
```

**Implementation:**
```python
async def json_body_parser(request: Request, response: Response, anext: Anext):
    if request.method not in ("POST", "PUT", "PATCH"):
        return await anext()
    try:
        body_bytes = await request.get_body()
        if not body_bytes:
            return await anext()
        request.body = json.loads(body_bytes.decode("utf-8"))
        await anext()
    except json.JSONDecodeError:
        response.set_status_code(400)
        await response.send_json({"error": "Invalid JSON"})
```

### `cors_middleware`

Adds CORS headers to responses and handles OPTIONS preflight requests.

**Usage:**
```python
from nextpress import Nextpress
from nextpress.middlewares import cors_middleware

app = Nextpress()

# Apply to all routes
app.use("/*", cors_middleware)

# Or to specific routes
app.get("/api/data", cors_middleware, get_data)
```

**Features:**
- Sets `Access-Control-Allow-Origin: *`
- Sets `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`
- Sets `Access-Control-Allow-Headers: Content-Type, Authorization`
- Automatically responds to OPTIONS requests with 204 No Content

**Implementation:**
```python
async def cors_middleware(request: Request, response: Response, anext: Anext):
    response.set_header("Access-Control-Allow-Origin", "*")
    response.set_header(
        "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
    )
    response.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    if request.method == "OPTIONS":
        response.set_status_code(204)
        await response.send_text("")
    else:
        await anext()
```

**Customizing CORS:**

For custom CORS settings, create your own middleware:

```python
async def custom_cors(request: Request, response: Response, anext: Anext):
    response.set_header("Access-Control-Allow-Origin", "https://myapp.com")
    response.set_header("Access-Control-Allow-Credentials", "true")
    response.set_header("Access-Control-Allow-Methods", "GET, POST")
    if request.method == "OPTIONS":
        response.set_status_code(204)
        await response.send_text("")
    else:
        await anext()
```

## Creating Custom Middleware

### Logger Middleware

Log all requests with timing:

```python
import time
from nextpress import Request, Response, Anext

async def logger(request: Request, response: Response, anext: Anext):
    start_time = time.time()
    print(f"--> {request.method} {request.path}")

    await anext()

    duration = time.time() - start_time
    print(f"<-- {request.method} {request.path} ({duration:.3f}s)")

app.use("/*", logger)
```

### Authentication Middleware

Verify authentication tokens:

```python
async def auth_middleware(request: Request, response: Response, anext: Anext):
    token = request.query_params.get("token")

    if not token:
        response.set_status_code(401)
        await response.send_json({"error": "Authentication required"})
        return  # Don't call anext() - stop execution

    # Verify token (simplified)
    if token != "secret-token":
        response.set_status_code(403)
        await response.send_json({"error": "Invalid token"})
        return

    # Token is valid, continue
    await anext()

# Apply to protected routes
app.get("/admin/users", auth_middleware, get_users)
app.post("/admin/users", auth_middleware, json_body_parser, create_user)
```

### Request ID Middleware

Add unique request IDs:

```python
import uuid

async def request_id_middleware(request: Request, response: Response, anext: Anext):
    request_id = str(uuid.uuid4())
    response.set_header("X-Request-ID", request_id)
    response.local_state["request_id"] = request_id

    await anext()

app.use("/*", request_id_middleware)
```

### Rate Limiting Middleware

Simple rate limiting:

```python
from time import time
from collections import defaultdict

# In-memory store (use Redis in production)
rate_limit_store = defaultdict(list)

async def rate_limiter(request: Request, response: Response, anext: Anext):
    client_ip = "127.0.0.1"  # Get from request in real app
    now = time()
    window = 60  # 60 seconds
    max_requests = 10

    # Clean old requests
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip]
        if now - t < window
    ]

    # Check limit
    if len(rate_limit_store[client_ip]) >= max_requests:
        response.set_status_code(429)
        await response.send_json({"error": "Rate limit exceeded"})
        return

    # Add this request
    rate_limit_store[client_ip].append(now)

    await anext()

app.use("/*", rate_limiter)
```

### Error Handling Middleware

Catch and handle errors:

```python
async def error_handler(request: Request, response: Response, anext: Anext):
    try:
        await anext()
    except ValueError as e:
        response.set_status_code(400)
        await response.send_json({"error": str(e)})
    except KeyError as e:
        response.set_status_code(400)
        await response.send_json({"error": f"Missing field: {e}"})
    except Exception as e:
        print(f"Unexpected error: {e}")
        response.set_status_code(500)
        await response.send_json({"error": "Internal server error"})

app.use("/*", error_handler)
```

### Response Time Header

Add processing time to response headers:

```python
import time

async def response_time(request: Request, response: Response, anext: Anext):
    start = time.time()
    await anext()
    duration = time.time() - start
    response.set_header("X-Response-Time", f"{duration:.3f}s")

app.use("/*", response_time)
```

## Middleware Patterns

### Conditional Middleware

Execute middleware based on conditions:

```python
async def conditional_auth(request: Request, response: Response, anext: Anext):
    # Skip auth for public endpoints
    if request.path.startswith("/public"):
        return await anext()

    # Check auth for other endpoints
    token = request.query_params.get("token")
    if not token:
        response.set_status_code(401)
        await response.send_json({"error": "Auth required"})
        return

    await anext()
```

### Middleware Factories

Create configurable middleware:

```python
def create_logger(prefix: str):
    async def logger(request: Request, response: Response, anext: Anext):
        print(f"{prefix}: {request.method} {request.path}")
        await anext()
    return logger

# Use with different configurations
app.get("/api/v1/users", create_logger("[API v1]"), get_users)
app.get("/api/v2/users", create_logger("[API v2]"), get_users_v2)
```

### Composing Middleware

Combine multiple middleware:

```python
def compose_middleware(*middlewares):
    async def composed(request: Request, response: Response, anext: Anext):
        # Execute all middleware in order
        for middleware in middlewares:
            # Each middleware gets the same request/response
            await middleware(request, response, anext)
    return composed

# Compose auth and logging
protected_route = compose_middleware(auth_middleware, logger)
app.get("/admin", protected_route, admin_handler)
```

### Dependency Injection Pattern

Pass data between middleware using `response.local_state`:

```python
async def load_user(request: Request, response: Response, anext: Anext):
    user_id = request.query_params.get("user_id")
    # Load user from database
    user = {"id": user_id, "name": "John"}
    response.local_state["user"] = user
    await anext()

async def require_admin(request: Request, response: Response, anext: Anext):
    user = response.local_state.get("user")
    if not user or not user.get("is_admin"):
        response.set_status_code(403)
        await response.send_json({"error": "Admin access required"})
        return
    await anext()

async def admin_handler(response: Response):
    user = response.local_state["user"]
    await response.send_json({"message": f"Hello admin {user['name']}"})

app.get("/admin", load_user, require_admin, admin_handler)
```

### Global vs. Route-Specific Middleware

```python
# Global middleware - applies to all routes
app.use("/*", logger)
app.use("/*", cors_middleware)

# Route-specific middleware
app.get("/public", public_handler)  # Only logger and CORS
app.get("/admin", auth_middleware, admin_handler)  # Logger, CORS, and auth
app.post("/data", json_body_parser, process_data)  # Logger, CORS, and JSON parsing
```

## Best Practices

1. **Order Matters**: Place global middleware (logger, CORS) first
2. **Error Handling**: Wrap middleware chains in error handlers
3. **Don't Forget `anext()`**: Always call `await anext()` unless intentionally stopping
4. **Use `local_state`**: Share data between middleware using `response.local_state`
5. **Keep It Simple**: Each middleware should do one thing well
6. **Type Safety**: Use generic types for better IDE support
7. **Testing**: Test middleware in isolation

## Testing Middleware

Example test for custom middleware:

```python
import pytest
from nextpress import Request, Response

@pytest.mark.asyncio
async def test_auth_middleware():
    # Mock objects
    request = Request(method="GET", path="/test", receive=lambda: {})
    response = Response(asgi_send=lambda x: None)

    anext_called = False
    async def mock_anext():
        nonlocal anext_called
        anext_called = True

    # Test without token
    await auth_middleware(request, response, mock_anext)
    assert response._status_code == 401
    assert not anext_called

    # Test with valid token
    request.query_params = {"token": "secret-token"}
    await auth_middleware(request, response, mock_anext)
    assert anext_called
```
