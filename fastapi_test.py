import fastapi

app = fastapi.FastAPI()


@app.get("/users/{user_id}")
async def root(user_id: str):
    return "user_id/{user_id}"


@app.get("/users/{user_id}/details")
async def details(user_id: str):
    return "/users/{user_id}/details"


@app.get("/users/{user_id}/{method}")
async def method(user_id: str):
    return "/users/{user_id}/{method}"


@app.get("/users/all")
async def all_users():
    return "/users/all"


@app.get("/users/{user_id}/info")
async def info(user_id: str):
    return "/users/{user_id}/info"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
