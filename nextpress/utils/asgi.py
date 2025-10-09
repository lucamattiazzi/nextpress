from typing import Callable


def asgi_send_body(asgi_send: Callable, body: str | bytes, more_body: bool = False):
    body = body if isinstance(body, bytes) else body.encode("utf-8")
    return asgi_send(
        {
            "type": "http.response.body",
            "body": body,
            "more_body": more_body,
        }
    )


def asgi_send_headers(
    asgi_send: Callable, status_code: int, headers: list[tuple[bytes, bytes]]
):
    return asgi_send(
        {
            "type": "http.response.start",
            "status": status_code,
            "headers": headers,
        }
    )
