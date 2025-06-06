import typing
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from tortoise import Tortoise
from tortoise.contrib.fastapi import RegisterTortoise

from backend.models import Log
from backend.routes.api import api_router
from backend.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with RegisterTortoise(
        app=app,
        db_url=settings.DB_URL,
        modules={"models": ["backend.models"]},
        generate_schemas=True,
    ):
        yield
        await Tortoise.close_connections()


app = FastAPI(title="SAE401-Back", lifespan=lifespan)
app.include_router(api_router)


@app.middleware("http")
async def create_log_entry(
    request: Request, call_next: typing.Callable[[Request], typing.Awaitable[Response]]
):
    response = await call_next(request)
    if response.status_code == 307:
        # Ignore redirection
        return response
    await Log.create(
        ip=request.client.host if request.client else None,
        chemin=request.url.path,
        code_reponse=response.status_code,
    )
    return response
