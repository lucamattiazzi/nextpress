from itertools import chain
from typing import Callable

from nextpress.errors import error_404
from nextpress.response import Response
from nextpress.types import Request, Route
from nextpress.utils import get_best_routes


async def next():
    pass


class Nextpress:
    routes = []

    def __init__(self):
        pass

    def get(self, route: str, *args: list[Route]):
        new_route = Route(method="GET", match=route, handlers=args)
        self.routes.append(new_route)

    def post(self, route: str, *args: list[Route]):
        new_route = Route(method="POST", match=route, handlers=args)
        self.routes.append(new_route)

    def use(self, route: str, *args: list[Route]):
        new_route = Route(method="*", match=route, handlers=args)
        self.routes.append(new_route)

    async def http(self, scope: dict, receive: Callable, send: Callable):
        path = scope.get("path", "")
        method = scope.get("method", "GET")
        valid_routes = [route for route in self.routes if route.method in [method, "*"]]
        best_matches = get_best_routes(path, valid_routes)

        response = Response(asgi_send=send)
        request = Request(method=method, path=path, get_body=receive)

        all_handlers = chain.from_iterable([route.handlers for route in best_matches])
        all_handlers = list(all_handlers)
        if not all_handlers:
            return await error_404(response)
        for handler in all_handlers:
            await handler(request, response, next)
        await response.end()

    async def lifespan(self, scope: dict, receive: Callable, send: Callable):
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})

    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        HANDLERS = {
            "http": self.http,
            "lifespan": self.lifespan,
        }
        handler = HANDLERS.get(scope["type"])
        if handler is None:
            raise NotImplementedError(f"Unknown scope type {scope['type']}")
        await handler(scope, receive, send)
