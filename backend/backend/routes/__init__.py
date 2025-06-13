from fastapi import APIRouter
from tortoise.contrib.pydantic import pydantic_model_creator

from backend.models import Log
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


@api_router.get("/logs", response_model=list[pydantic_model_creator(Log)])
async def get_logs(limit: int = 10, ip: str | None = None) -> list[Log]:
    """Obtiens les logs les plus récents.

    Parameters
    ----------
    limit : int, optionnel

        Le nombre de logs à récupéré, limité à 100, par défaut 10

    Returns
    -------
    Retourne la liste des logs
    """
    op = Log.all().limit(limit).order_by("-date_creation")
    if limit > 100:
        limit = 100
    if ip:
        op = op.filter(ip=ip)
    logs = await op
    return logs
