import time

from nextpress import Nextpress

app = Nextpress()


async def root(request, response, next):
    await response.send("Hello, World!")


async def api(request, response, next):
    method = request.method
    await response.json({"message": f"API endpoint accessed with {method} method"})


async def logger(request, response, next):
    print(f"{request.method} {request.path}")
    response.set_header("X-Processed-Time", str(time.time()))
    await next()


async def part_1(request, response, next):
    await response.send("Part 1 completed. ")
    time.sleep(1)
    await next()


async def part_2(request, response, next):
    await response.send("Part 2 completed. ")
    await response.end()


app.get("/", root)
app.use("/api", logger, api)
app.get("/double", part_1, part_2)
