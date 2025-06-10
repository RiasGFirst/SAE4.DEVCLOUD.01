from fastapi import APIRouter

from backend.routes import account, transaction, user

api_router = APIRouter(prefix="/api")
api_router.include_router(user.router, prefix="/user", tags=["User"])
api_router.include_router(account.router, prefix="/account", tags=["Account"])
api_router.include_router(
    transaction.router, prefix="/transaction", tags=["Transaction"]
)


@api_router.get("/ping")
async def ping():
    return "pong"
