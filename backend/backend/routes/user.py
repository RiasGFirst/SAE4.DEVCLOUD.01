from typing import Annotated

import pydantic
from fastapi import APIRouter, HTTPException, Response, status
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import IntegrityError

from backend.auth import CurrentUser
from backend.models import (
    Compte,
    Operation,
    TypeCompte,
    TypeUtilisateur,
    Utilisateur,
    ValidationCompte,
)

router = APIRouter()


@router.get("", response_model=list[pydantic_model_creator(Utilisateur)])
async def list_users():
    """Liste tous les utilisateurs créés."""
    users = await Utilisateur.all()
    return users


class CreateUserPayload(pydantic.BaseModel):
    """Payload pour la création d'un utilisateur."""

    nom: str
    email: str
    mot_de_passe: str
    role: TypeUtilisateur


class CreateUserResponse(pydantic.BaseModel):
    user: Annotated[Utilisateur, pydantic_model_creator(Utilisateur)]
    account: Annotated[Compte, pydantic_model_creator(Compte)] | None


@router.post("", response_model=CreateUserResponse)
async def create_user(payload: CreateUserPayload):
    """Crée un nouveeau utilisateur en fonction des paramètres donnés."""
    try:
        user = await Utilisateur.create(
            nom=payload.nom,
            email=payload.email,
            password=payload.mot_de_passe,
            role=payload.role,
        )
        if user.role == TypeUtilisateur.USER:
            compte = await Compte.create(
                utilisateur=user,
                type_compte=TypeCompte.COURANT,
                solde=0,
            )
            await ValidationCompte.create(compte=compte, valide=True, agent=None)
        else:
            compte = None
        return {"user": user, "account": compte}
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User already exists"
        )


@router.get("/me", response_model=pydantic_model_creator(Utilisateur))
async def get_user(user: CurrentUser):
    return user


@router.get(
    "/me/recent",
    response_model=dict[str, list[pydantic_model_creator(Operation)]],
)
async def get_recent_operations(user: CurrentUser, limit: int = 5):
    await user.fetch_related("comptes")
    operations: dict[str, list[Operation]] = {}
    for compte in user.comptes:
        operations[compte.iban] = (
            await Operation.filter_by_account(compte)
            .limit(limit)
            .order_by("-date_creation")
        )
    return operations


@router.delete("/me", response_model=None)
async def delete_user(user: CurrentUser):
    """Supprime le utilisateur connecté."""
    await user.delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
