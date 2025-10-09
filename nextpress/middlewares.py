import json

from nextpress.types import Anext, Request, Response


async def json_body_parser(request: Request, response: Response, anext: Anext):
    if request.method not in ("POST", "PUT", "PATCH"):
        return await anext()
    try:
        body_bytes = await request.get_body()
        if not body_bytes:
            return await anext()
        request.body = json.loads(body_bytes.decode("utf-8"))
        await anext()
    except json.JSONDecodeError:
        response.set_status_code(400)
        await response.send_json({"error": "Invalid JSON"})


async def cors_middleware(request: Request, response: Response, anext: Anext):
    response.set_header("Access-Control-Allow-Origin", "*")
    response.set_header(
        "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
    )
    response.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    if request.method == "OPTIONS":
        response.set_status_code(204)
        await response.send()
    else:
        await anext()
