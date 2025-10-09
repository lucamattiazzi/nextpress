import re
from typing import Callable

from nextpress.types import Request, Response, Route


def get_best_route(method: str, pattern: str, routes: list[Route]) -> Route:
    valid_routes = [route for route in routes if route.method in [method, "*"]]
    exact_matches = [route for route in valid_routes if route.match == pattern]
    if exact_matches:
        return exact_matches[0]
    regex_matches = [route for route in valid_routes if re.search(pattern, route.match)]
    if regex_matches:
        return regex_matches[0]
    return []


async def run_middlewares(
    middlewares: list[Callable], request: Request, response: Response
) -> None:
    current_idx = 0

    async def anext():
        nonlocal current_idx
        if current_idx >= len(middlewares):
            return await response.end()
        handler = middlewares[current_idx]
        current_idx += 1
        params = {}
        if "request" in handler.__annotations__:
            params["request"] = request
        if "response" in handler.__annotations__:
            params["response"] = response
        if "anext" in handler.__annotations__:
            params["anext"] = anext
        await handler(**params)

    await anext()
