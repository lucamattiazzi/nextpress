import json
import time
from typing import TypedDict

import pytest

from nextpress import Anext, Nextpress, Request, Response
from nextpress.middlewares import cors_middleware, json_body_parser


class UserPayload(TypedDict):
    name: str
    age: int


class MessageResponse(TypedDict):
    message: str


@pytest.fixture
def app():
    """Create a basic test application"""
    app = Nextpress()

    async def root(response: Response):
        await response.send_text("Hello, World!")

    async def get_users(response: Response):
        await response.send_json({"users": ["Alice", "Bob", "Charlie"]})

    async def create_user(
        request: Request[UserPayload], response: Response[MessageResponse]
    ):
        body = request.body
        name = body.get("name", "Guest") if body else "Guest"
        await response.send_json({"message": f"User {name} created"})

    async def get_user_by_id(request: Request, response: Response):
        # Note: route_params would be populated by routing logic
        await response.send_json({"id": "placeholder", "name": "Test User"})

    async def echo_query_params(request: Request, response: Response):
        await response.send_json(request.query_params)

    async def custom_headers(response: Response):
        response.set_header("X-Custom-Header", "test-value")
        response.set_status_code(201)
        await response.send_text("Custom response")

    async def error_handler(response: Response):
        raise ValueError("Intentional error")

    app.get("/", root)
    app.get("/users", get_users)
    app.post("/users", json_body_parser, create_user)
    app.get("/users/:id", get_user_by_id)
    app.get("/echo", echo_query_params)
    app.get("/custom", custom_headers)
    app.get("/error", error_handler)

    return app


class TestIntegrationBasicRoutes:
    @pytest.mark.asyncio
    async def test_root_endpoint(self, app):
        sent_data = []

        async def mock_receive():
            return {"body": b"", "more_body": False}

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        assert sent_data[0]["status"] == 200
        assert sent_data[1]["body"] == b"Hello, World!"

    @pytest.mark.asyncio
    async def test_json_response(self, app):
        sent_data = []

        async def mock_receive():
            return {"body": b"", "more_body": False}

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/users",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        assert sent_data[0]["status"] == 200
        headers_dict = dict(sent_data[0]["headers"])
        assert b"application/json" in headers_dict[b"Content-Type"]
        response_body = json.loads(sent_data[1]["body"])
        assert response_body == {"users": ["Alice", "Bob", "Charlie"]}

    @pytest.mark.asyncio
    async def test_query_params(self, app):
        sent_data = []

        async def mock_receive():
            return {"body": b"", "more_body": False}

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/echo",
            "query_string": b"name=Alice&age=30",
        }

        await app(scope, mock_receive, mock_send)

        response_body = json.loads(sent_data[1]["body"])
        assert response_body == {"name": "Alice", "age": "30"}

    @pytest.mark.asyncio
    async def test_custom_headers_and_status(self, app):
        sent_data = []

        async def mock_receive():
            return {"body": b"", "more_body": False}

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/custom",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        assert sent_data[0]["status"] == 201
        headers_dict = dict(sent_data[0]["headers"])
        assert headers_dict[b"X-Custom-Header"] == b"test-value"

    @pytest.mark.asyncio
    async def test_404_not_found(self, app):
        sent_data = []

        async def mock_receive():
            return {}

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/nonexistent",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        assert sent_data[0]["status"] == 404
        assert sent_data[1]["body"] == b"page not found!"


class TestIntegrationPostRequests:
    @pytest.mark.asyncio
    async def test_post_with_json_body(self, app):
        sent_data = []
        body_data = {"name": "Alice", "age": 25}

        async def mock_receive():
            return {
                "body": json.dumps(body_data).encode("utf-8"),
                "more_body": False,
            }

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/users",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        assert sent_data[0]["status"] == 200
        response_body = json.loads(sent_data[1]["body"])
        assert response_body == {"message": "User Alice created"}

    @pytest.mark.asyncio
    async def test_post_with_invalid_json(self, app):
        sent_data = []

        async def mock_receive():
            return {"body": b"invalid json {", "more_body": False}

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/users",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        assert sent_data[0]["status"] == 400
        response_body = json.loads(sent_data[1]["body"])
        assert response_body == {"error": "Invalid JSON"}


class TestIntegrationMiddleware:
    @pytest.mark.asyncio
    async def test_middleware_chain(self):
        app = Nextpress()
        call_order = []

        async def logger_middleware(request: Request, response: Response, anext: Anext):
            call_order.append("logger-before")
            response.set_header("X-Request-Id", "12345")
            await anext()
            call_order.append("logger-after")

        async def auth_middleware(request: Request, response: Response, anext: Anext):
            call_order.append("auth-before")
            response.local_state["user"] = "test_user"
            await anext()
            call_order.append("auth-after")

        async def handler(response: Response):
            call_order.append("handler")
            user = response.local_state.get("user", "anonymous")
            await response.send_json({"user": user})

        app.get("/protected", logger_middleware, auth_middleware, handler)

        sent_data = []

        async def mock_receive():
            return {"body": b"", "more_body": False}

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/protected",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        # Verify execution order
        assert call_order == [
            "logger-before",
            "auth-before",
            "handler",
            "auth-after",
            "logger-after",
        ]

        # Verify response
        assert sent_data[0]["status"] == 200
        headers_dict = dict(sent_data[0]["headers"])
        assert headers_dict[b"X-Request-Id"] == b"12345"
        response_body = json.loads(sent_data[1]["body"])
        assert response_body == {"user": "test_user"}

    @pytest.mark.asyncio
    async def test_cors_middleware(self):
        app = Nextpress()

        async def handler(response: Response):
            await response.send_text("OK")

        app.get("/api", cors_middleware, handler)

        sent_data = []

        async def mock_receive():
            return {"body": b"", "more_body": False}

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        headers_dict = dict(sent_data[0]["headers"])
        assert headers_dict[b"Access-Control-Allow-Origin"] == b"*"

    @pytest.mark.asyncio
    async def test_middleware_short_circuit(self):
        app = Nextpress()
        call_order = []

        async def blocking_middleware(
            request: Request, response: Response, anext: Anext
        ):
            call_order.append("blocking")
            response.set_status_code(403)
            await response.send_json({"error": "Forbidden"})
            # Don't call anext - short circuit

        async def handler(response: Response):
            call_order.append("handler")
            await response.send_text("Should not reach here")

        app.get("/blocked", blocking_middleware, handler)

        sent_data = []

        async def mock_receive():
            return {"body": b"", "more_body": False}

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/blocked",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        # Handler should not have been called
        assert call_order == ["blocking"]
        assert sent_data[0]["status"] == 403


class TestIntegrationErrorHandling:
    @pytest.mark.asyncio
    async def test_error_returns_500(self, app):
        sent_data = []

        async def mock_receive():
            return {"body": b"", "more_body": False}

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/error",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        assert sent_data[0]["status"] == 500
        assert sent_data[1]["body"] == b"internal server error!"


class TestIntegrationComplexScenarios:
    @pytest.mark.asyncio
    async def test_full_request_response_cycle(self):
        app = Nextpress()

        async def timing_middleware(request: Request, response: Response, anext: Anext):
            start_time = time.time()
            await anext()
            elapsed = time.time() - start_time
            response.local_state["elapsed"] = elapsed

        async def create_item(request: Request[dict], response: Response[dict]):
            body = request.body or {}
            item_name = body.get("name", "Unknown")
            await response.send_json(
                {
                    "id": 123,
                    "name": item_name,
                    "created": True,
                }
            )

        app.post("/items", json_body_parser, timing_middleware, create_item)

        sent_data = []
        body_data = {"name": "Test Item"}

        async def mock_receive():
            return {
                "body": json.dumps(body_data).encode("utf-8"),
                "more_body": False,
            }

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/items",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        assert sent_data[0]["status"] == 200
        response_body = json.loads(sent_data[1]["body"])
        assert response_body["name"] == "Test Item"
        assert response_body["created"] is True

    @pytest.mark.asyncio
    async def test_multiple_different_routes(self):
        app = Nextpress()

        async def get_home(response: Response):
            await response.send_text("Home")

        async def get_about(response: Response):
            await response.send_text("About")

        async def post_contact(request: Request, response: Response):
            await response.send_json({"submitted": True})

        app.get("/", get_home)
        app.get("/about", get_about)
        app.post("/contact", json_body_parser, post_contact)

        # Test each route
        for method, path, expected_status in [
            ("GET", "/", 200),
            ("GET", "/about", 200),
            ("POST", "/contact", 200),
        ]:
            sent_data = []

            async def mock_receive():
                return {"body": b"{}", "more_body": False}

            async def mock_send(data):
                sent_data.append(data)

            scope = {
                "type": "http",
                "method": method,
                "path": path,
                "query_string": b"",
            }

            await app(scope, mock_receive, mock_send)
            assert sent_data[0]["status"] == expected_status
