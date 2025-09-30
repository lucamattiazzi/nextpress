from nextpress.response import Response


async def error_404(response: Response):
    response.set_status(404)
    await response.end("page not found!")
