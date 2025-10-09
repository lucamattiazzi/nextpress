from typing import Callable


async def error_404(send: Callable):
    await send({"type": "http.response.start", "status": 404, "headers": []})
    await send({"type": "http.response.body", "body": b"page not found!"})


async def error_500(send: Callable):
    await send({"type": "http.response.start", "status": 500, "headers": []})
    await send({"type": "http.response.body", "body": b"internal server error!"})
