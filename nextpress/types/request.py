from typing import Callable

from pydantic import BaseModel


class Request[InputT](BaseModel):
    body: InputT | None = None
    method: str
    path: str
    receive: Callable
    query_params: dict = {}

    async def get_body(self) -> bytes:
        body = b""
        more_body = True

        while more_body:
            message = await self.receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        return body
