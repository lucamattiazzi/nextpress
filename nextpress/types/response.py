import json
from typing import Callable

from pydantic import BaseModel

from nextpress.utils.asgi import asgi_send_body, asgi_send_headers


class Response[OutputT](BaseModel):
    asgi_send: Callable
    body: OutputT | None = None
    local_state: dict = {}

    _headers_buffer: list[tuple[bytes, bytes]] = []
    _status_code: int = 200

    _response_closed: bool = False
    _headers_sent: bool = False
    _is_chunked: bool = False

    ## private
    def _set_header(self, key: str, value: str):
        self._headers_buffer.append(
            (bytes(key.encode("utf-8")), bytes(value.encode("utf-8")))
        )

    async def _send_headers(self):
        if self._headers_sent:
            return
        await asgi_send_headers(self.asgi_send, self._status_code, self._headers_buffer)
        self._headers_sent = True
        self._headers_buffer = []

    async def _send_body(self, content: str | bytes, content_type: str = "text/plain"):
        if isinstance(content, str):
            content = content.encode("utf-8")
        self._set_header("Content-Type", content_type)
        self._set_header("Content-Length", str(len(content)))
        await self._send_headers()
        await asgi_send_body(self.asgi_send, content, more_body=True)
        await self.end()

    ## public
    def set_header(self, key: str, value: str):
        if self._headers_sent:
            raise RuntimeError("Headers already sent")
        self._set_header(key, value)

    def set_status_code(self, status_code: int):
        if self._headers_sent:
            raise RuntimeError("Headers already sent")
        self._status_code = status_code

    async def send_bytes(self, content: bytes):
        await self._send_body(content, content_type="application/octet-stream")

    async def send_text(self, content: str):
        await self._send_body(content, content_type="text/plain; charset=utf-8")

    async def send_json(self, content: dict):
        content_str = json.dumps(content)
        await self._send_body(
            content_str, content_type="application/json; charset=utf-8"
        )

    async def write(self, content: str | bytes):
        self._is_chunked = True
        if isinstance(content, str):
            self._set_header("Content-Type", "text/plain; charset=utf-8")
            self._set_header("Transfer-Encoding", "chunked")
            await self._send_headers()
        await asgi_send_body(self.asgi_send, content.encode("utf-8"), more_body=True)

        return await self._write_bytes(content)

    async def end(self, content: str = ""):
        if self._response_closed:
            return

        if not self._is_chunked and content:
            return await self._send_body(content)

        if self._is_chunked and content:
            await self.write(content)
            await asgi_send_body(self.asgi_send, b"", more_body=False)
            self._response_closed = True
            return

        if not self._headers_sent:
            self._set_header("Content-Length", str(len(content)))
            self._set_header("Content-Type", "text/plain; charset=utf-8")
            await self._send_headers()

        await asgi_send_body(self.asgi_send, content, more_body=False)
        self._response_closed = True
