import pytest

from nextpress.entities import Request, Response, Route
from nextpress.utils.routes import extract_route_params, find_best_route, sort_routes


class TestRoute:
    def test_route_initialization(self):
        async def handler(request: Request, response: Response):
            pass

        route = Route(method="GET", match="/test", handlers=[handler])

        assert route.method == "GET"
        assert route.match == "/test"
        assert len(route.handlers) == 1
        assert route.params == []

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
        )

        assert route.params == ["id"]

    def test_route_wildcard_method(self):
        async def handler(request: Request, response: Response):
            pass

        route = Route(method="*", match="/middleware", handlers=[handler])

        assert route.method == "*"

    def test_route_empty_handlers(self):
        route = Route(method="GET", match="/", handlers=[])

        assert len(route.handlers) == 0

    def test_route_requires_method(self):
        with pytest.raises(TypeError):
            Route(match="/test", handlers=[])

    def test_route_requires_match(self):
        with pytest.raises(TypeError):
            Route(method="GET", handlers=[])

    def test_route_requires_handlers(self):
        with pytest.raises(TypeError):
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


class TestRouteUtils:
    def test_sort_routes(self):
        async def handler():
            pass

        route1 = Route(method="GET", match="/users/:id", handlers=[handler])
        route2 = Route(
            method="GET", match="/posts/:postId/comments/:commentId", handlers=[handler]
        )
        route3 = Route(method="GET", match="/about", handlers=[handler])

        routes = [route1, route2, route3]
        sorted_routes = sort_routes(routes)

        assert sorted_routes == [route3, route1, route2]

    def test_extract_route_params(self):
        async def handler():
            pass

        route = Route(
            method="GET", match="/users/:id/posts/:postId", handlers=[handler]
        )
        path = "/users/123/posts/456"

        params = extract_route_params(route, path)

        assert params == {"id": "123", "postId": "456"}

    def test_find_best_route(self):
        async def handler():
            pass

        route1 = Route(method="GET", match="/users/:id", handlers=[handler])
        route2 = Route(
            method="GET", match="/posts/:postId/comments/:commentId", handlers=[handler]
        )
        route3 = Route(method="GET", match="/about", handlers=[handler])

        routes = [route1, route2, route3]

        best_route = find_best_route(routes, "GET", "/posts/789/comments/101")

        assert best_route == route2

    def test_find_least_params_route(self):
        async def handler():
            pass

        route1 = Route(method="GET", match="/users/:id/info", handlers=[handler])
        route2 = Route(method="GET", match="/users/me/info", handlers=[handler])
        route3 = Route(method="GET", match="/about", handlers=[handler])

        routes = [route1, route2, route3]

        best_route = find_best_route(routes, "GET", "/users/me/info")

        assert best_route == route2
