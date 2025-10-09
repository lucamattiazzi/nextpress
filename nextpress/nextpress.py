from typing import Callable

from nextpress.errors import error_404, error_500
from nextpress.types import Request, Response, Route
from nextpress.utils.server import (
    get_best_route,
    run_middlewares,
)
from nextpress.utils.types import (
    extract_query_params,
    extract_request_type,
    extract_response_type,
)


class Nextpress:
    routes = []

    def __init__(self):
        pass

    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        HANDLERS = {
            "http": self._http,
            "lifespan": self._lifespan,
        }
        handler = HANDLERS.get(scope["type"])
        if handler is None:
            raise NotImplementedError(f"Unknown scope type {scope['type']}")
        await handler(scope, receive, send)

    ## PUBLIC

    def get(self, route: str, *args: list[Route]):
        new_route = Route(method="GET", match=route, handlers=args)
        self.routes.append(new_route)

    def post(self, route: str, *args: list[Route]):
        new_route = Route(method="POST", match=route, handlers=args)
        self.routes.append(new_route)

    def patch(self, route: str, *args: list[Route]):
        new_route = Route(method="PATCH", match=route, handlers=args)
        self.routes.append(new_route)

    def put(self, route: str, *args: list[Route]):
        new_route = Route(method="PUT", match=route, handlers=args)
        self.routes.append(new_route)

    def delete(self, route: str, *args: list[Route]):
        new_route = Route(method="DELETE", match=route, handlers=args)
        self.routes.append(new_route)

    def options(self, route: str, *args: list[Route]):
        new_route = Route(method="OPTIONS", match=route, handlers=args)
        self.routes.append(new_route)

    def use(self, route: str, *args: list[Route]):
        new_route = Route(method="*", match=route, handlers=args)
        self.routes.append(new_route)

    ## PRIVATE
    async def _http(self, scope: dict, receive: Callable, send: Callable):
        try:
            path = scope.get("path", "")
            method = scope.get("method", "GET")
            best_match = get_best_route(method, path, self.routes)
            if not best_match:
                return await error_404(send)

            request_type = extract_request_type(best_match.handlers)
            response_type = extract_response_type(best_match.handlers)
            query_params = extract_query_params(scope.get("query_string", b""))
            request = Request[request_type](
                method=method,
                path=path,
                receive=receive,
                route_params=best_match.route_params,
                query_params=query_params,
            )
            response = Response[response_type](asgi_send=send)
            await run_middlewares(best_match.handlers, request, response)

        except Exception as e:
            print(f"Error: {e}")
            await error_500(send)

    async def _lifespan(self, scope: dict, receive: Callable, send: Callable):
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
