# Advanced Usage

Advanced patterns and techniques for building applications with Nextpress.

## Table of Contents

- [Streaming Responses](#streaming-responses)
- [Error Handling](#error-handling)
- [Request/Response Type Safety](#requestresponse-type-safety)
- [Application Structure](#application-structure)
- [Performance Optimization](#performance-optimization)
- [Testing](#testing)
- [Deployment](#deployment)

## Streaming Responses

Nextpress supports streaming responses using chunked transfer encoding.

### Basic Streaming

Use `response.write()` for streaming and `response.end()` to finish:

```python
from asyncio import sleep
from nextpress import Response

async def stream_handler(response: Response):
    # Start streaming
    await response.write("Chunk 1\n")
    await sleep(1)

    await response.write("Chunk 2\n")
    await sleep(1)

    await response.write("Chunk 3\n")

    # End the stream
    await response.end()

app.get("/stream", stream_handler)
```

### Server-Sent Events (SSE)

Implement Server-Sent Events for real-time updates:

```python
from asyncio import sleep

async def sse_handler(response: Response):
    response.set_header("Content-Type", "text/event-stream")
    response.set_header("Cache-Control", "no-cache")
    response.set_header("Connection", "keep-alive")

    # Send events
    for i in range(10):
        event = f"data: {{'count': {i}}}\n\n"
        await response.write(event)
        await sleep(1)

    await response.end()

app.get("/events", sse_handler)
```

### Large File Streaming

Stream large files without loading them into memory:

```python
async def download_file(response: Response):
    response.set_header("Content-Type", "application/octet-stream")
    response.set_header("Content-Disposition", "attachment; filename=largefile.bin")

    # Stream file in chunks
    with open("largefile.bin", "rb") as f:
        while chunk := f.read(8192):  # 8KB chunks
            await response.write(chunk)

    await response.end()

app.get("/download", download_file)
```

### Progress Updates

Stream progress updates for long-running operations:

```python
import json
from asyncio import sleep

async def long_operation(response: Response):
    response.set_header("Content-Type", "application/x-ndjson")

    total_steps = 100
    for step in range(total_steps):
        # Simulate work
        await sleep(0.1)

        # Send progress update
        progress = {
            "step": step + 1,
            "total": total_steps,
            "percentage": ((step + 1) / total_steps) * 100
        }
        await response.write(json.dumps(progress) + "\n")

    await response.end()

app.get("/process", long_operation)
```

## Error Handling

### Global Error Handler

Create a global error handler middleware:

```python
from nextpress import Request, Response, Anext

async def global_error_handler(request: Request, response: Response, anext: Anext):
    try:
        await anext()
    except ValueError as e:
        response.set_status_code(400)
        await response.send_json({
            "error": "Bad Request",
            "message": str(e)
        })
    except PermissionError as e:
        response.set_status_code(403)
        await response.send_json({
            "error": "Forbidden",
            "message": str(e)
        })
    except FileNotFoundError as e:
        response.set_status_code(404)
        await response.send_json({
            "error": "Not Found",
            "message": str(e)
        })
    except Exception as e:
        # Log the error
        print(f"Unexpected error: {type(e).__name__}: {e}")

        # Don't expose internal errors to clients
        response.set_status_code(500)
        await response.send_json({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        })

# Apply globally
app.use("/*", global_error_handler)
```

### Custom Exception Classes

Define custom exceptions for different error cases:

```python
class AppError(Exception):
    """Base exception for application errors"""
    status_code = 500
    message = "An error occurred"

class NotFoundError(AppError):
    status_code = 404
    message = "Resource not found"

class ValidationError(AppError):
    status_code = 400
    message = "Validation failed"

class UnauthorizedError(AppError):
    status_code = 401
    message = "Authentication required"

# Error handler that understands custom exceptions
async def error_handler(request: Request, response: Response, anext: Anext):
    try:
        await anext()
    except AppError as e:
        response.set_status_code(e.status_code)
        await response.send_json({
            "error": e.__class__.__name__,
            "message": str(e) or e.message
        })
    except Exception as e:
        print(f"Unexpected error: {e}")
        response.set_status_code(500)
        await response.send_json({
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        })

app.use("/*", error_handler)

# Use in handlers
async def get_user(request: Request, response: Response):
    user_id = request.query_params.get("id")
    if not user_id:
        raise ValidationError("User ID is required")

    user = find_user(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")

    await response.send_json(user)
```

### Validation with Error Handling

Combine validation with proper error responses:

```python
from typing import TypedDict

class CreateUserData(TypedDict):
    name: str
    email: str
    age: int

def validate_user_data(data: dict) -> CreateUserData:
    if not data.get("name"):
        raise ValidationError("Name is required")

    if not data.get("email"):
        raise ValidationError("Email is required")

    if "@" not in data.get("email", ""):
        raise ValidationError("Invalid email format")

    age = data.get("age")
    if age is not None and (not isinstance(age, int) or age < 0):
        raise ValidationError("Age must be a positive integer")

    return data

async def create_user(request: Request[dict], response: Response):
    # Validation raises ValidationError which is caught by error_handler
    user_data = validate_user_data(request.body)

    # Create user...
    response.set_status_code(201)
    await response.send_json({"user": user_data})

app.post("/users", json_body_parser, create_user)
```

## Request/Response Type Safety

### Type-Safe Handlers

Use Python's type system for better IDE support and runtime safety:

```python
from typing import TypedDict

class UserQuery(TypedDict, total=False):
    page: str
    limit: str
    search: str

class User(TypedDict):
    id: int
    name: str
    email: str

class UserListResponse(TypedDict):
    users: list[User]
    total: int
    page: int

async def list_users(
    request: Request,
    response: Response[UserListResponse]
):
    # Type-safe query parameters
    page = int(request.query_params.get("page", "1"))
    limit = int(request.query_params.get("limit", "10"))

    # Fetch users...
    users: list[User] = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
    ]

    # Type-safe response
    await response.send_json({
        "users": users,
        "total": len(users),
        "page": page
    })

app.get("/users", list_users)
```

### Pydantic Models (Future)

While Nextpress uses Pydantic internally, you can also use Pydantic models for validation:

```python
from pydantic import BaseModel, EmailStr, validator

class CreateUserModel(BaseModel):
    name: str
    email: EmailStr
    age: int

    @validator('age')
    def age_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Age must be positive')
        return v

async def validate_with_pydantic(request: Request, response: Response, anext: Anext):
    try:
        # Parse and validate with Pydantic
        model = CreateUserModel(**request.body)
        # Store validated data
        request.body = model.model_dump()
        await anext()
    except Exception as e:
        response.set_status_code(400)
        await response.send_json({"error": str(e)})

app.post("/users", json_body_parser, validate_with_pydantic, create_user)
```

## Application Structure

### Modular Application Design

Structure larger applications into modules:

```
myapp/
├── app.py              # Main application
├── routes/
│   ├── __init__.py
│   ├── users.py        # User routes
│   ├── posts.py        # Post routes
│   └── auth.py         # Auth routes
├── middlewares/
│   ├── __init__.py
│   ├── auth.py         # Auth middleware
│   └── logging.py      # Logging middleware
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── post.py
└── utils/
    ├── __init__.py
    └── validation.py
```

**app.py:**
```python
from nextpress import Nextpress
from routes import users, posts, auth
from middlewares.logging import logger
from middlewares.auth import auth_middleware

app = Nextpress()

# Global middleware
app.use("/*", logger)

# Register route modules
users.register_routes(app)
posts.register_routes(app)
auth.register_routes(app)
```

**routes/users.py:**
```python
from nextpress import Request, Response
from nextpress.middlewares import json_body_parser
from middlewares.auth import auth_middleware

async def get_users(response: Response):
    users = [{"id": 1, "name": "Alice"}]
    await response.send_json({"users": users})

async def create_user(request: Request, response: Response):
    user_data = request.body
    # Create user...
    response.set_status_code(201)
    await response.send_json({"user": user_data})

def register_routes(app):
    app.get("/users", get_users)
    app.post("/users", auth_middleware, json_body_parser, create_user)
```

### Route Prefixing

Create route groups with common prefixes:

```python
class Router:
    def __init__(self, app: Nextpress, prefix: str, middlewares: list = None):
        self.app = app
        self.prefix = prefix
        self.middlewares = middlewares or []

    def get(self, path: str, *handlers):
        all_handlers = [*self.middlewares, *handlers]
        self.app.get(f"{self.prefix}{path}", *all_handlers)

    def post(self, path: str, *handlers):
        all_handlers = [*self.middlewares, *handlers]
        self.app.post(f"{self.prefix}{path}", *all_handlers)

# Use it
api_v1 = Router(app, "/api/v1", middlewares=[logger, auth_middleware])
api_v1.get("/users", get_users)
api_v1.post("/users", json_body_parser, create_user)

api_v2 = Router(app, "/api/v2", middlewares=[logger])
api_v2.get("/users", get_users_v2)
```

## Performance Optimization

### Async Best Practices

Leverage async properly for better performance:

```python
import asyncio

# Good - concurrent operations
async def fetch_user_data(response: Response):
    # Run multiple async operations concurrently
    user_task = fetch_user_from_db()
    posts_task = fetch_user_posts()
    stats_task = fetch_user_stats()

    user, posts, stats = await asyncio.gather(
        user_task,
        posts_task,
        stats_task
    )

    await response.send_json({
        "user": user,
        "posts": posts,
        "stats": stats
    })

# Bad - sequential operations
async def fetch_user_data_slow(response: Response):
    user = await fetch_user_from_db()
    posts = await fetch_user_posts()  # Waits for user first
    stats = await fetch_user_stats()  # Waits for posts first
```

### Response Caching

Implement caching middleware:

```python
from functools import lru_cache
import time

cache = {}

def create_cache_middleware(ttl: int = 60):
    async def cache_middleware(request: Request, response: Response, anext: Anext):
        # Only cache GET requests
        if request.method != "GET":
            return await anext()

        cache_key = f"{request.method}:{request.path}"
        now = time.time()

        # Check cache
        if cache_key in cache:
            cached_data, timestamp = cache[cache_key]
            if now - timestamp < ttl:
                response.set_header("X-Cache", "HIT")
                return await response.send_json(cached_data)

        # Store original send_json
        original_send = response.send_json

        # Intercept send_json to cache response
        async def cached_send(data):
            cache[cache_key] = (data, now)
            response.set_header("X-Cache", "MISS")
            await original_send(data)

        response.send_json = cached_send
        await anext()

    return cache_middleware

# Use caching
app.get("/expensive-data", create_cache_middleware(ttl=300), get_expensive_data)
```

## Testing

### Unit Testing Handlers

Test handlers in isolation:

```python
import pytest
from unittest.mock import AsyncMock
from nextpress import Request, Response

@pytest.mark.asyncio
async def test_get_users():
    # Create mock response
    send_mock = AsyncMock()
    response = Response(asgi_send=send_mock)

    # Call handler
    await get_users(response)

    # Verify response
    assert send_mock.called
    # Check the response data
```

### Integration Testing

Test complete request/response cycle:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users",
            json={"name": "Alice", "email": "alice@example.com"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["name"] == "Alice"

@pytest.mark.asyncio
async def test_auth_required():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/admin/users")
        assert response.status_code == 401
```

### Testing with Fixtures

Use pytest fixtures for common test setup:

```python
@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}

@pytest.mark.asyncio
async def test_with_fixtures(client, auth_headers):
    response = await client.get("/admin/users", headers=auth_headers)
    assert response.status_code == 200
```

## Deployment

### Production Server

Use uvicorn with production settings:

```bash
# Basic production run
uvicorn app:app --host 0.0.0.0 --port 8000

# With workers for better performance
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4

# With uvloop for better async performance
pip install uvloop
uvicorn app:app --host 0.0.0.0 --port 8000 --loop uvloop
```

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

# Copy application
COPY . .

# Run server
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    restart: unless-stopped
```

### Nginx Reverse Proxy

Configure Nginx as a reverse proxy:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment Configuration

Manage configuration with environment variables:

```python
import os

class Config:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    PORT = int(os.getenv("PORT", "8000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
    DATABASE_URL = os.getenv("DATABASE_URL")

config = Config()

# Use in application
if config.ENVIRONMENT == "production":
    # Production-specific settings
    pass
```

### Monitoring and Logging

Implement structured logging:

```python
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def structured_logger(request: Request, response: Response, anext: Anext):
    start_time = datetime.now()

    try:
        await anext()
        status = response._status_code
    except Exception as e:
        status = 500
        raise
    finally:
        duration = (datetime.now() - start_time).total_seconds()

        log_entry = {
            "timestamp": start_time.isoformat(),
            "method": request.method,
            "path": request.path,
            "status": status,
            "duration": duration,
        }

        logger.info(json.dumps(log_entry))

app.use("/*", structured_logger)
```

### Health Check Endpoint

Add health check for load balancers:

```python
async def health_check(response: Response):
    await response.send_json({
        "status": "healthy",
        "timestamp": time.time()
    })

app.get("/health", health_check)
```
