from fastapi import APIRouter

from backend.routes.api import user

api_router = APIRouter(prefix="/api")
api_router.include_router(user.router, prefix="/account", tags=["account"])


@api_router.get("/ping")
async def ping():
    return "pong"
