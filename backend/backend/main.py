from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import RegisterTortoise

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
