from typing import Annotated

import pydantic
from fastapi import APIRouter, HTTPException, Response, status
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import IntegrityError

from backend.auth import CurrentUser
from backend.models import Compte, DepotPydantic, RetraitPydantic, TypeCompte, VirementPydantic

router = APIRouter()


@router.get("/", response_model=list[pydantic_model_creator(Compte)])
async def list_accounts(user: CurrentUser):
    """Liste tous les comptes utilisateurs créés."""
    accounts = await Compte.filter(utilisateur=user)
    return accounts


class CreateAccountPayload(pydantic.BaseModel):
    """Payload pour la création d'un compte."""

    type: TypeCompte
    solde_initial: float = 0.0


@router.post("/", response_model=pydantic_model_creator(Compte))
async def create_account(user: CurrentUser, payload: CreateAccountPayload):
    """Crée un nouveeau compte en fonction des paramètres donnés."""
    try:
        account = await Compte.create(
            utilisateur=user,
            type_compte=payload.type,
            solde=payload.solde_initial,
        )
        return account
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account already exists"
        )


class GetAccountResponse(pydantic.BaseModel):
    """Modèle de réponse pour la récupération d'un compte utilisateur."""

    account: Annotated[Compte, pydantic_model_creator(Compte)]
    operations: list[RetraitPydantic | DepotPydantic | VirementPydantic]


@router.get("/{account_id}", response_model=GetAccountResponse)
async def get_account(account_id: int, user: CurrentUser):
    """Récupère un compte utilisateur spécifique."""
    account = await Compte.get_user_account(account_id, user)

    return {
        "account": account,
        "operations": await account.get_all_operations(),
    }


class AuthorizeAccountPayload(pydantic.BaseModel):
    """Payload pour la validation d'un compte."""
    authorize: bool


@router.post("/{account_id}/approval", response_model=pydantic_model_creator(Compte))
async def authorize_account(account_id: int, user: CurrentUser, payload: AuthorizeAccountPayload):
    user.can_authorize()

    account = await Compte.get_user_account(account_id, user)
    account.validated = payload.authorize
    await account.save()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me", response_model=None)
async def delete_user(user: CurrentUser):
    """Supprime le compte utilisateur connecté."""
    await user.delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
