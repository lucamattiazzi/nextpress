import pytest

from nextpress import Nextpress, Request, Response


class TestNextpress:
    def test_nextpress_initialization(self):
        app = Nextpress()
        assert app.routes == []

    def test_get_route_registration(self):
        app = Nextpress()

        async def handler(response: Response):
            pass

        app.get("/test", handler)

        assert len(app.routes) == 1
        assert app.routes[0].method == "GET"
        assert app.routes[0].match == "/test"
        assert len(app.routes[0].handlers) == 1

    def test_post_route_registration(self):
        app = Nextpress()

        async def handler(response: Response):
            pass

        app.post("/api", handler)

        assert len(app.routes) == 1
        assert app.routes[0].method == "POST"

    def test_put_route_registration(self):
        app = Nextpress()

        async def handler(response: Response):
            pass

        app.put("/update", handler)

        assert len(app.routes) == 1
        assert app.routes[0].method == "PUT"

    def test_patch_route_registration(self):
        app = Nextpress()

        async def handler(response: Response):
            pass

        app.patch("/modify", handler)

        assert len(app.routes) == 1
        assert app.routes[0].method == "PATCH"

    def test_delete_route_registration(self):
        app = Nextpress()

        async def handler(response: Response):
            pass

        app.delete("/remove", handler)

        assert len(app.routes) == 1
        assert app.routes[0].method == "DELETE"

    def test_options_route_registration(self):
        app = Nextpress()

        async def handler(response: Response):
            pass

        app.options("/info", handler)

        assert len(app.routes) == 1
        assert app.routes[0].method == "OPTIONS"

    def test_use_middleware_registration(self):
        app = Nextpress()

        async def middleware(request: Request, response: Response, anext):
            pass

        app.use("/", middleware)

        assert len(app.routes) == 1
        assert app.routes[0].method == "*"

    def test_multiple_handlers_registration(self):
        app = Nextpress()

        async def middleware(request: Request, response: Response, anext):
            pass

        async def handler(response: Response):
            pass

        app.get("/test", middleware, handler)

        assert len(app.routes) == 1
        assert len(app.routes[0].handlers) == 2

    def test_multiple_routes_registration(self):
        app = Nextpress()

        async def handler1(response: Response):
            pass

        async def handler2(response: Response):
            pass

        async def handler3(response: Response):
            pass

        app.get("/", handler1)
        app.post("/api", handler2)
        app.put("/update", handler3)

        assert len(app.routes) == 3

    @pytest.mark.asyncio
    async def test_http_handler_success(self):
        app = Nextpress()
        sent_data = []

        async def handler(response: Response):
            await response.send_text("Hello")

        app.get("/test", handler)

        async def mock_receive():
            return {"body": b"", "more_body": False}

        async def mock_send(data):
            sent_data.append(data)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        # Should have sent headers and body
        assert len(sent_data) > 0
        assert sent_data[0]["type"] == "http.response.start"
        assert sent_data[0]["status"] == 200

    @pytest.mark.asyncio
    async def test_http_handler_404_not_found(self):
        app = Nextpress()
        sent_data = []

        async def handler(response: Response):
            await response.send_text("Hello")

        app.get("/test", handler)

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

        # Should return 404
        assert sent_data[0]["status"] == 404
        assert sent_data[1]["body"] == b"page not found!"

    @pytest.mark.asyncio
    async def test_http_handler_with_query_params(self):
        app = Nextpress()
        captured_request = None

        async def handler(request: Request, response: Response):
            nonlocal captured_request
            captured_request = request
            await response.send_text("OK")

        app.get("/search", handler)

        async def mock_receive():
            return {"body": b"", "more_body": False}

        async def mock_send(data):
            pass

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/search",
            "query_string": b"q=test&limit=10",
        }

        await app(scope, mock_receive, mock_send)

        assert captured_request is not None
        assert captured_request.query_params["q"] == "test"
        assert captured_request.query_params["limit"] == "10"

    @pytest.mark.asyncio
    async def test_http_handler_with_post_body(self):
        app = Nextpress()
        captured_request = None

        async def handler(request: Request, response: Response):
            nonlocal captured_request
            captured_request = request
            await response.send_text("OK")

        app.post("/data", handler)

        body_data = b'{"name": "test"}'

        async def mock_receive():
            return {"body": body_data, "more_body": False}

        async def mock_send(data):
            pass

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/data",
            "query_string": b"",
        }

        await app(scope, mock_receive, mock_send)

        assert captured_request is not None
        assert captured_request.method == "POST"

    @pytest.mark.asyncio
    async def test_lifespan_startup(self):
        app = Nextpress()
        sent_data = []

        async def mock_receive():
            return {"type": "lifespan.startup"}

        async def mock_send(data):
            sent_data.append(data)
            # Simulate shutdown after startup
            if data["type"] == "lifespan.startup.complete":
                raise StopAsyncIteration

        scope = {"type": "lifespan"}

        try:
            await app(scope, mock_receive, mock_send)
        except StopAsyncIteration:
            pass

        assert len(sent_data) > 0
        assert sent_data[0]["type"] == "lifespan.startup.complete"

    @pytest.mark.asyncio
    async def test_lifespan_shutdown(self):
        app = Nextpress()
        sent_data = []

        async def mock_receive():
            return {"type": "lifespan.shutdown"}

        async def mock_send(data):
            sent_data.append(data)
            raise StopAsyncIteration

        scope = {"type": "lifespan"}

        try:
            await app(scope, mock_receive, mock_send)
        except StopAsyncIteration:
            pass

        assert len(sent_data) > 0
        assert sent_data[0]["type"] == "lifespan.shutdown.complete"

    @pytest.mark.asyncio
    async def test_unknown_scope_type_raises_error(self):
        app = Nextpress()

        scope = {"type": "websocket"}

        with pytest.raises(NotImplementedError, match="Unknown scope type"):
            await app(scope, lambda: None, lambda x: None)

    @pytest.mark.asyncio
    async def test_error_handling_returns_500(self):
        app = Nextpress()
        sent_data = []

        async def failing_handler(response: Response):
            raise ValueError("Something went wrong")

        app.get("/error", failing_handler)

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

        # Should return 500 error
        assert sent_data[0]["status"] == 500
        assert sent_data[1]["body"] == b"internal server error!"

    def test_route_order_preservation(self):
        app = Nextpress()

        async def handler1():
            pass

        async def handler2():
            pass

        async def handler3():
            pass

        app.get("/first", handler1)
        app.get("/second", handler2)
        app.get("/third", handler3)

        assert app.routes[0].match == "/first"
        assert app.routes[1].match == "/second"
        assert app.routes[2].match == "/third"
