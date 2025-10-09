import time
from asyncio import sleep
from typing import TypedDict

from nextpress import Anext, Nextpress, Request, Response
from nextpress.middlewares import json_body_parser

app = Nextpress()


class ApiResponsePayload(TypedDict):
    message: str


class DataResponsePayload(TypedDict):
    message: str


class DataRequestPayload(TypedDict):
    name: str


async def root(response: Response[str]):
    await response.send_text("Hello, World!")


async def logger(request: Request, response: Response, anext: Anext):
    print(f"{request.method} {request.path}")
    response.set_header("X-Processed-Time", str(time.time()))
    await anext()
    await sleep(5)
    print("Logger middleware finished")


async def api(response: Response[ApiResponsePayload], request: Request):
    method = request.method
    await response.send_json({"message": f"API endpoint accessed with {method} method"})


async def data(
    request: Request[DataRequestPayload], response: Response[DataResponsePayload]
):
    body = request.body
    name = body.get("name", "Guest") if body else "Guest"
    body = f"Hello, {name}!"
    await response.send_json({"message": body})


app.get("/", root)
app.get("/api", logger, api)
app.post("/data", json_body_parser, data)
