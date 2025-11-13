from asyncio import sleep

import pytest

from nextpress.entities import Anext, Request, Response, Route
from nextpress.utils.routes import find_best_route
from nextpress.utils.server import run_middlewares


class TestGetBestRoute:
    def test_exact_match(self):
        routes = [
            Route(method="GET", match="/", handlers=[]),
            Route(method="GET", match="/api", handlers=[]),
            Route(method="POST", match="/api", handlers=[]),
        ]

        result = find_best_route(routes, "GET", "/api")
        assert result.method == "GET"
        assert result.match == "/api"

    def test_wildcard_method(self):
        routes = [
            Route(method="*", match="/middleware", handlers=[]),
            Route(method="GET", match="/api", handlers=[]),
        ]

        result = find_best_route(routes, "POST", "/middleware")
        assert result.method == "*"
        assert result.match == "/middleware"

    def test_no_match_returns_none(self):
        routes = [
            Route(method="GET", match="/", handlers=[]),
            Route(method="POST", match="/api", handlers=[]),
        ]

        result = find_best_route(routes, "GET", "/nonexistent")
        assert result is None

    def test_method_mismatch_returns_none(self):
        routes = [
            Route(method="GET", match="/api", handlers=[]),
            Route(method="POST", match="/data", handlers=[]),
        ]

        result = find_best_route(routes, "DELETE", "/api")
        assert result is None

    def test_prefers_exact_match_over_regex(self):
        routes = [
            Route(method="GET", match="/api/:param", handlers=[lambda: "regex"]),
            Route(method="GET", match="/api/users", handlers=[lambda: "exact"]),
        ]

        result = find_best_route(routes, "GET", "/api/users")
        assert result.match == "/api/users"

    def test_returns_first_wildcard_match(self):
        routes = [
            Route(method="*", match="/first", handlers=[]),
            Route(method="*", match="/second", handlers=[]),
        ]

        result = find_best_route(routes, "PATCH", "/first")
        assert result.match == "/first"

    def test_no_matching_route(self):
        routes = []

        result = find_best_route(routes, "GET", "/any")
        assert result is None


class TestRunMiddlewares:
    @pytest.mark.asyncio
    async def test_single_handler_no_annotations(self):
        called = []

        async def handler():
            called.append("handler")

        mock_send = lambda x: None
        request = Request(method="GET", path="/", receive=lambda: None)
        response = Response(asgi_send=mock_send)

        await run_middlewares([handler], request, response)
        assert called == ["handler"]

    @pytest.mark.asyncio
    async def test_handler_with_request_annotation(self):
        received_request = None

        async def handler(request: Request):
            nonlocal received_request
            received_request = request

        mock_send = lambda x: None
        request = Request(method="GET", path="/test", receive=lambda: None)
        response = Response(asgi_send=mock_send)

        await run_middlewares([handler], request, response)
        assert received_request is request
        assert received_request.path == "/test"

    @pytest.mark.asyncio
    async def test_handler_with_response_annotation(self):
        received_response = None

        async def handler(response: Response):
            nonlocal received_response
            received_response = response

        mock_send = lambda x: None
        request = Request(method="GET", path="/", receive=lambda: None)
        response = Response(asgi_send=mock_send)

        await run_middlewares([handler], request, response)
        assert received_response is response

    @pytest.mark.asyncio
    async def test_middleware_chain_with_anext(self):
        call_order = []

        async def middleware1(request: Request, response: Response, anext: Anext):
            call_order.append("before-1")
            await anext()
            await sleep(0.1)
            call_order.append("after-1")

        async def middleware2(request: Request, response: Response, anext: Anext):
            call_order.append("before-2")
            await anext()
            await sleep(0.1)
            call_order.append("after-2")

        async def handler(request: Request, response: Response):
            call_order.append("handler")

        mock_send = lambda x: None
        request = Request(method="GET", path="/", receive=lambda: None)
        response = Response(asgi_send=mock_send)

        await run_middlewares([middleware1, middleware2, handler], request, response)
        assert call_order == [
            "before-1",
            "before-2",
            "handler",
            "after-2",
            "after-1",
        ]

    @pytest.mark.asyncio
    async def test_middleware_stops_chain_without_anext(self):
        call_order = []

        async def middleware1(request: Request, response: Response, anext: Anext):
            call_order.append("middleware1")
            # Don't call anext - stops the chain
            pass

        async def handler(request: Request, response: Response):
            call_order.append("handler")

        async def mock_send(x):
            pass

        request = Request(method="GET", path="/", receive=lambda: None)
        response = Response(asgi_send=mock_send)

        await run_middlewares([middleware1, handler], request, response)
        assert call_order == ["middleware1"]
        assert "handler" not in call_order

    @pytest.mark.asyncio
    async def test_mixed_annotations(self):
        results = {}

        async def handler1(request: Request, anext: Anext):
            results["request"] = request.path
            await anext()

        async def handler2(response: Response, anext: Anext):
            results["response"] = True
            await anext()

        async def handler3(anext: Anext):
            results["no_params"] = True
            await anext()

        async def mock_send(x):
            pass

        request = Request(method="GET", path="/test", receive=lambda: None)
        response = Response(asgi_send=mock_send)

        await run_middlewares([handler1, handler2, handler3], request, response)
        assert results == {"request": "/test", "response": True, "no_params": True}

    @pytest.mark.asyncio
    async def test_empty_middleware_list(self):
        mock_send = lambda x: None
        request = Request(method="GET", path="/", receive=lambda: None)
        response = Response(asgi_send=mock_send)

        # Should complete without error
        await run_middlewares([], request, response)
