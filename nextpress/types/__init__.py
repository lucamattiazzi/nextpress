from typing import Awaitable, Callable

from pydantic import BaseModel

from nextpress.types.request import Request
from nextpress.types.response import Response

type RouteHandler = Callable[[Request, Response], Awaitable]


class Route(BaseModel):
    method: str
    match: str
    handlers: list[RouteHandler]
    route_params: dict[str, str] = {}


type Anext = Callable[[], Awaitable]

__all__ = ["Route", "Anext", "RouteHandler", "Request", "Response"]
