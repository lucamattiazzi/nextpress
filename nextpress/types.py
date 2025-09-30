from typing import Callable

from pydantic import BaseModel

from nextpress.response import Response


class Request(BaseModel):
    method: str
    path: str
    get_body: Callable


type Next = Callable[[], None]


type RouteHandler = Callable[[Request, Response, Next], None]


class Route(BaseModel):
    method: str
    match: str
    handlers: list[RouteHandler]
