# API Reference

Complete API reference for Nextpress.

## Table of Contents

- [Nextpress Class](#nextpress-class)
- [Request Class](#request-class)
- [Response Class](#response-class)
- [Types](#types)
- [Utility Functions](#utility-functions)

## Nextpress Class

The main application class for creating a web server.

### Constructor

```python
app = Nextpress()
```

Creates a new Nextpress application instance.

### Routing Methods

#### `app.get(route: str, *handlers)`

Register handlers for GET requests.

**Parameters:**
- `route` (str): URL pattern to match
- `*handlers`: One or more async handler functions

**Example:**
```python
app.get("/users", get_users)
app.get("/users/:id", auth_middleware, get_user)
```

#### `app.post(route: str, *handlers)`

Register handlers for POST requests.

**Parameters:**
- `route` (str): URL pattern to match
- `*handlers`: One or more async handler functions

**Example:**
```python
app.post("/users", json_body_parser, create_user)
```

#### `app.put(route: str, *handlers)`

Register handlers for PUT requests.

**Parameters:**
- `route` (str): URL pattern to match
- `*handlers`: One or more async handler functions

**Example:**
```python
app.put("/users/:id", json_body_parser, update_user)
```

#### `app.patch(route: str, *handlers)`

Register handlers for PATCH requests.

**Parameters:**
- `route` (str): URL pattern to match
- `*handlers`: One or more async handler functions

**Example:**
```python
app.patch("/users/:id", json_body_parser, partial_update_user)
```

#### `app.delete(route: str, *handlers)`

Register handlers for DELETE requests.

**Parameters:**
- `route` (str): URL pattern to match
- `*handlers`: One or more async handler functions

**Example:**
```python
app.delete("/users/:id", auth_middleware, delete_user)
```

#### `app.options(route: str, *handlers)`

Register handlers for OPTIONS requests.

**Parameters:**
- `route` (str): URL pattern to match
- `*handlers`: One or more async handler functions

**Example:**
```python
app.options("/users", cors_options)
```

#### `app.use(route: str, *handlers)`

Register middleware for all HTTP methods.

**Parameters:**
- `route` (str): URL pattern to match
- `*handlers`: One or more async middleware functions

**Example:**
```python
app.use("/*", logger)
app.use("/api/*", auth_middleware)
```

### Route Patterns

Routes support exact matching and regex patterns:

```python
# Exact match
app.get("/users", handler)

# With path parameters (using route_params)
app.get("/users/:id", handler)

# Wildcard
app.get("/api/*", handler)
```

## Request Class

The Request object provides access to incoming request data.

### Type Parameters

```python
Request[InputT]
```

Generic type for the request body. Use `TypedDict` or other types for type safety.

### Properties

#### `method: str`

The HTTP method of the request (GET, POST, etc.).

```python
async def handler(request: Request):
    method = request.method  # "GET", "POST", etc.
```

#### `path: str`

The request path.

```python
async def handler(request: Request):
    path = request.path  # "/users/123"
```

#### `body: InputT | None`

The parsed request body. Set by middleware like `json_body_parser`.

```python
class UserData(TypedDict):
    name: str

async def handler(request: Request[UserData]):
    name = request.body["name"]  # Type-safe
```

#### `query_params: dict`

Query string parameters as a dictionary.

```python
async def handler(request: Request):
    page = request.query_params.get("page", "1")
    # /users?page=2 -> page = "2"
```

#### `route_params: dict[str, str]`

Path parameters extracted from the route pattern.

```python
# Route: /users/:id
async def handler(request: Request):
    user_id = request.route_params.get("id")
    # /users/123 -> user_id = "123"
```

#### `receive: Callable`

ASGI receive callable. Used internally, rarely needed in application code.

### Methods

#### `async get_body() -> bytes`

Get the raw request body as bytes.

```python
async def handler(request: Request):
    raw_body = await request.get_body()
    # b'{"name": "John"}'
```

**Returns:** The complete request body as bytes.

**Note:** This method reads the entire body into memory. For large uploads, consider streaming approaches.

## Response Class

The Response object provides methods to send data to the client.

### Type Parameters

```python
Response[OutputT]
```

Generic type for the response body. Use `TypedDict` or other types for type safety.

### Properties

#### `body: OutputT | None`

The response body value (for type checking purposes).

#### `local_state: dict`

A dictionary for storing arbitrary data during request processing. Useful for passing data between middleware.

```python
async def middleware(response: Response, anext: Anext):
    response.local_state["user_id"] = 123
    await anext()

async def handler(response: Response):
    user_id = response.local_state.get("user_id")
```

### Methods

#### `set_header(key: str, value: str)`

Set a response header.

```python
async def handler(response: Response):
    response.set_header("X-Custom-Header", "value")
    response.set_header("Cache-Control", "no-cache")
    await response.send_text("Hello")
```

**Parameters:**
- `key` (str): Header name
- `value` (str): Header value

**Raises:** `RuntimeError` if headers have already been sent.

**Note:** Must be called before sending the response.

#### `set_status_code(status_code: int)`

Set the HTTP status code.

```python
async def handler(response: Response):
    response.set_status_code(201)
    await response.send_json({"created": True})
```

**Parameters:**
- `status_code` (int): HTTP status code (200, 404, 500, etc.)

**Raises:** `RuntimeError` if headers have already been sent.

#### `async send_text(content: str)`

Send a text response with `text/plain` content type.

```python
async def handler(response: Response):
    await response.send_text("Hello, World!")
```

**Parameters:**
- `content` (str): The text content to send

**Note:** Automatically sets `Content-Type: text/plain; charset=utf-8` and `Content-Length`.

#### `async send_json(content: dict)`

Send a JSON response with `application/json` content type.

```python
async def handler(response: Response):
    await response.send_json({
        "message": "Success",
        "data": [1, 2, 3]
    })
```

**Parameters:**
- `content` (dict): Dictionary to serialize as JSON

**Note:** Automatically sets `Content-Type: application/json; charset=utf-8` and `Content-Length`.

#### `async send_bytes(content: bytes)`

Send binary data with `application/octet-stream` content type.

```python
async def handler(response: Response):
    image_data = open("image.png", "rb").read()
    await response.send_bytes(image_data)
```

**Parameters:**
- `content` (bytes): Binary data to send

**Note:** Automatically sets `Content-Type: application/octet-stream` and `Content-Length`.

#### `async write(content: str | bytes)`

Write a chunk of data using chunked transfer encoding. Useful for streaming responses.

```python
async def handler(response: Response):
    await response.write("Chunk 1\n")
    await response.write("Chunk 2\n")
    await response.end("Final chunk")
```

**Parameters:**
- `content` (str | bytes): Data chunk to write

**Note:** Automatically sets `Transfer-Encoding: chunked`. Must call `end()` when finished.

#### `async end(content: str = "")`

End the response, optionally sending final content.

```python
async def handler(response: Response):
    response.set_header("X-Custom", "value")
    await response.end("Done!")
```

**Parameters:**
- `content` (str, optional): Final content to send

**Note:** Called automatically by `send_text()`, `send_json()`, and `send_bytes()`.

## Types

### `Anext`

Type alias for the `anext` function passed to middleware.

```python
type Anext = Callable[[], Awaitable]
```

**Usage:**
```python
async def middleware(request: Request, response: Response, anext: Anext):
    # Do something before
    await anext()  # Continue to next handler
    # Do something after
```

### `Route`

Internal model representing a registered route.

```python
class Route(BaseModel):
    method: str
    match: str
    handlers: list[RouteHandler]
    route_params: dict[str, str] = {}
```

### `RouteHandler`

Type alias for route handler functions.

```python
type RouteHandler = Callable[[Request, Response], Awaitable]
```

## Utility Functions

### Route Matching

#### `get_best_route(method: str, pattern: str, routes: list[Route]) -> Route`

Internal function to find the best matching route for a request.

**Parameters:**
- `method` (str): HTTP method
- `pattern` (str): Request path
- `routes` (list[Route]): List of registered routes

**Returns:** The best matching Route object, or empty list if no match.

### Middleware Execution

#### `async run_middlewares(middlewares: list[Callable], request: Request, response: Response) -> None`

Internal function to execute a chain of middleware/handlers.

**Parameters:**
- `middlewares` (list[Callable]): List of handlers to execute
- `request` (Request): Request object
- `response` (Response): Response object

### Type Extraction

#### `extract_request_type(handlers: list[Callable]) -> type`

Extract the generic type parameter from Request type hints in handlers.

#### `extract_response_type(handlers: list[Callable]) -> type`

Extract the generic type parameter from Response type hints in handlers.

#### `extract_query_params(query_string: bytes) -> dict[str, str]`

Parse query string into a dictionary.

**Parameters:**
- `query_string` (bytes): Raw query string from ASGI scope

**Returns:** Dictionary of query parameters

**Example:**
```python
extract_query_params(b"page=1&limit=10")
# Returns: {"page": "1", "limit": "10"}

extract_query_params(b"tags=python&tags=web")
# Returns: {"tags": ["python", "web"]}
```

## Error Handling

### Built-in Error Handlers

#### `async error_404(send: Callable)`

Send a 404 Not Found response.

#### `async error_500(send: Callable)`

Send a 500 Internal Server Error response.

### Custom Error Handling

Wrap routes in try-except blocks:

```python
async def handler(response: Response):
    try:
        # Your code
        result = risky_operation()
        await response.send_json({"result": result})
    except ValueError as e:
        response.set_status_code(400)
        await response.send_json({"error": str(e)})
    except Exception as e:
        response.set_status_code(500)
        await response.send_json({"error": "Internal error"})
```

Or create error handling middleware:

```python
async def error_handler(request: Request, response: Response, anext: Anext):
    try:
        await anext()
    except Exception as e:
        response.set_status_code(500)
        await response.send_json({"error": str(e)})

app.use("/*", error_handler)
```
