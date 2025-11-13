from typing import Callable

from nextpress.entities import Request, Response


async def run_middlewares(
    middlewares: list[Callable], request: Request, response: Response
) -> None:
    if not len(middlewares):
        return

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
