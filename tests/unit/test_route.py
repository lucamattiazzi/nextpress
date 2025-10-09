import pytest
from pydantic import ValidationError

from nextpress.types import Route, Request, Response


class TestRoute:
    def test_route_initialization(self):
        async def handler(request: Request, response: Response):
            pass

        route = Route(method="GET", match="/test", handlers=[handler])

        assert route.method == "GET"
        assert route.match == "/test"
        assert len(route.handlers) == 1
        assert route.route_params == {}

    def test_route_with_multiple_handlers(self):
        async def middleware(request: Request, response: Response, anext):
            pass

        async def handler(request: Request, response: Response):
            pass

        route = Route(method="POST", match="/api", handlers=[middleware, handler])

        assert route.method == "POST"
        assert len(route.handlers) == 2

    def test_route_with_route_params(self):
        async def handler(request: Request, response: Response):
            pass

        route = Route(
            method="GET",
            match="/users/:id",
            handlers=[handler],
            route_params={"id": "123"},
        )

        assert route.route_params == {"id": "123"}

    def test_route_wildcard_method(self):
        async def handler(request: Request, response: Response):
            pass

        route = Route(method="*", match="/middleware", handlers=[handler])

        assert route.method == "*"

    def test_route_empty_handlers(self):
        route = Route(method="GET", match="/", handlers=[])

        assert len(route.handlers) == 0

    def test_route_requires_method(self):
        with pytest.raises(ValidationError):
            Route(match="/test", handlers=[])

    def test_route_requires_match(self):
        with pytest.raises(ValidationError):
            Route(method="GET", handlers=[])

    def test_route_requires_handlers(self):
        with pytest.raises(ValidationError):
            Route(method="GET", match="/test")

    def test_route_different_http_methods(self):
        async def handler():
            pass

        methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]

        for method in methods:
            route = Route(method=method, match="/test", handlers=[handler])
            assert route.method == method

    def test_route_complex_path(self):
        async def handler():
            pass

        route = Route(
            method="GET", match="/api/v1/users/:id/posts/:postId", handlers=[handler]
        )

        assert route.match == "/api/v1/users/:id/posts/:postId"

    def test_route_params_can_be_updated(self):
        async def handler():
            pass

        route = Route(method="GET", match="/users/:id", handlers=[handler])

        assert route.route_params == {}

        route.route_params = {"id": "456", "name": "test"}
        assert route.route_params == {"id": "456", "name": "test"}
