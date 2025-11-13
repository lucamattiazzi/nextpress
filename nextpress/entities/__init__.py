import re
from re import Pattern
from typing import Awaitable, Callable

from pydantic import BaseModel

from nextpress.entities.request import Request
from nextpress.entities.response import Response

type RouteHandler = Callable[[Request, Response], Awaitable]


class Route(BaseModel):
    method: str
    match: str
    pattern: Pattern
    handlers: list[RouteHandler]
    params: list[str]

    def __init__(self, method: str, match: str, handlers: list[RouteHandler], **data):
        pattern_str = re.sub(r":(\w+)", r"(?P<\1>[^/]+)", match)
        pattern_str = f"^{pattern_str}$"
        pattern = re.compile(pattern_str)
        params = list(pattern.groupindex.keys())

        super().__init__(
            method=method,
            match=match,
            pattern=pattern,
            handlers=list(handlers),
            params=params,
            **data,
        )


type Anext = Callable[[], Awaitable]

__all__ = ["Route", "Anext", "RouteHandler", "Request", "Response"]
