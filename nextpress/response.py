import json
from typing import Callable

from pydantic import BaseModel


class Response(BaseModel):
    asgi_send: Callable

    _headers_buffer: list[tuple[bytes, bytes]] = []
    _status_code: int = 200

    _response_closed: bool = False
    _headers_sent: bool = False

    def _set_header(self, key: str, value: str):
        self._headers_buffer.append(
            (bytes(key.encode("utf-8")), bytes(value.encode("utf-8")))
        )

    def set_header(self, key: str, value: str):
        if self._headers_sent:
            raise RuntimeError("Headers already sent")
        self._set_header(key, value)

    def set_status(self, status_code: int):
        if self._headers_sent:
            raise RuntimeError("Headers already sent")
        self._status_code = status_code

    async def _send_headers(self):
        if self._headers_sent:
            return
        await self.asgi_send(
            {
                "type": "http.response.start",
                "status": self._status_code,
                "headers": self._headers_buffer,
            }
        )
        self._headers_sent = True
        self._headers_buffer = []

    async def send(self, content: str):
        self._set_header("Content-Type", "text/plain; charset=utf-8")
        await self._send_headers()
        await self.asgi_send(
            {
                "type": "http.response.body",
                "body": bytes(content.encode("utf-8")),
                "more_body": True,
            }
        )

    async def json(self, content: dict):
        content_str = json.dumps(content)
        self._set_header("Content-Length", str(len(content_str)))
        self._set_header("Content-Type", "application/json; charset=utf-8")
        await self._send_headers()

        await self.asgi_send(
            {
                "type": "http.response.body",
                "body": bytes(content_str.encode("utf-8")),
                "more_body": True,
            }
        )

    async def end(self, content: str = ""):
        if self._response_closed:
            return
        if not self._headers_sent:
            self._set_header("Content-Length", str(len(content)))
            self._set_header("Content-Type", "text/plain; charset=utf-8")
            await self._send_headers()
        await self.asgi_send(
            {
                "type": "http.response.body",
                "body": bytes(content.encode("utf-8")),
                "more_body": False,
            }
        )
        self._response_closed = True
