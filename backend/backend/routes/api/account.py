from typing import Annotated

import pydantic
from fastapi import APIRouter, HTTPException, status
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import IntegrityError

from backend.auth import CurrentUser
from backend.models import Compte, Operation, TypeCompte

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
    operations: list[Annotated[Operation, pydantic_model_creator(Operation)]]


@router.get("/{account_id}", response_model=GetAccountResponse)
async def get_account(account_id: int, user: CurrentUser):
    """Récupère un compte utilisateur spécifique."""
    account = await Compte.filter(id=account_id, utilisateur=user).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )

    return {
        "account": account,
        "operations": await account.get_operations(),
    }


class CreateOperationOnlyAmountPayload(pydantic.BaseModel):
    """Payload pour la création d'une opération."""

    montant: float


@router.post(
    "/{account_id}/depot",
    response_model=Annotated[Operation, pydantic_model_creator(Operation)],
    tags=["Operation", "Account"],
)
async def create_deposit_operation(
    account_id: int, user: CurrentUser, payload: CreateOperationOnlyAmountPayload
):
    """Crée une opération de dépôt sur un compte utilisateur.

    Cette requête permet d'ajouter de l'argent à un compte.
    Elle vérifie que le montant est positif et que le compte existe.

    En cas d'échec, une erreur de validation HTTP 400 est levée.
    """
    account = await Compte.get_user_account(account_id, user)

    if payload.montant <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive"
        )

    operation = await Operation.create(
        compte_envoi=None,
        compte_reception=account,
        montant=payload.montant,
    )

    return operation


class CreateOperationVirementPayload(pydantic.BaseModel):
    """Payload pour la création d'une opération vers un compte."""

    compte_reception: int
    montant: float


@router.post(
    "/{account_id}/virement",
    response_model=Annotated[Operation, pydantic_model_creator(Operation)],
    tags=["Operation", "Account"],
)
async def create_operation(
    account_id: int, user: CurrentUser, payload: CreateOperationVirementPayload
):
    """Crée une opération sur un compte utilisateur.

    Cette requête permet de transférer de l'argent d'un compte à un autre.
    Elle vérifie donc que les comptes existent, que le montant est positif,
    et que le compte source a suffisamment de fonds.

    En cas d'échec, une erreur de validation HTTP 400 est levée.
    """
    account = await Compte.filter(id=account_id, utilisateur=user).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source account not found"
        )

    if account.id == payload.compte_reception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer to the same account",
        )

    compte_reception = await Compte.filter(id=payload.compte_reception).first()
    if not compte_reception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination account not found",
        )

    if payload.montant <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive"
        )
    if account.solde < payload.montant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance"
        )

    operation = await Operation.create(
        compte_envoi=account,
        compte_reception=compte_reception,
        montant=payload.montant,
    )

    return operation


# @router.delete("/me", response_model=None)
# async def delete_user(user: CurrentUser):
#     """Supprime le compte utilisateur connecté."""
#     await user.delete()
#     return Response(status_code=status.HTTP_204_NO_CONTENT)
