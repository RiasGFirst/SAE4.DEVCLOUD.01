from decimal import Decimal
from typing import Annotated

import pydantic
from fastapi import APIRouter, HTTPException, status
from tortoise.contrib.pydantic import pydantic_model_creator

from backend.auth import CurrentUser
from backend.models import Compte, Depot, Retrait, Virement

router = APIRouter()


class CreateOperationOnlyAmountPayload(pydantic.BaseModel):
    """Payload pour la création d'une opération."""

    montant: float


@router.post(
    "/{account_id}/depot",
    response_model=Annotated[Depot, pydantic_model_creator(Depot)]
)
async def create_deposit_operation(
    account_id: int, user: CurrentUser, payload: CreateOperationOnlyAmountPayload
):
    """Crée une opération de dépôt sur un compte utilisateur.

    Cette requête permet d'ajouter de l'argent à un compte.
    Elle vérifie que le montant est positif et que le compte existe.

    En cas d'échec, une erreur de validation HTTP 400 est levée.

    Le dépot est directement accepté.
    """
    account = await Compte.get_user_account(account_id, user)
    account.ensure_validated()

    if payload.montant <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive"
        )

    operation = await Depot.create(compte=account, montant=payload.montant)
    account.solde += Decimal(payload.montant)
    await account.save()

    return operation


@router.post(
    "/{account_id}/retrait",
    response_model=Annotated[Retrait, pydantic_model_creator(Retrait)]
)
async def create_withdrawal_operation(
    account_id: int, user: CurrentUser, payload: CreateOperationOnlyAmountPayload
):
    account = await Compte.get_user_account(account_id, user)
    account.ensure_validated()

    if payload.montant <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive"
        )

    if account.solde < payload.montant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance"
        )

    operation = await Retrait.create(compte=account, montant=payload.montant)
    return operation


class CreateOperationVirementPayload(pydantic.BaseModel):
    """Payload pour la création d'une opération vers un compte."""

    compte_reception: int
    montant: float


@router.post(
    "/{account_id}/virement",
    response_model=Annotated[Virement, pydantic_model_creator(Virement)]
)
async def create_virement(
    account_id: int, user: CurrentUser, payload: CreateOperationVirementPayload
):
    """Crée une opération sur un compte utilisateur.

    Cette requête permet de transférer de l'argent d'un compte à un autre.
    Elle vérifie donc que les comptes existent, que le montant est positif,
    et que le compte source a suffisamment de fonds.

    En cas d'échec, une erreur de validation HTTP 400 est levée.
    """
    if payload.montant <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive"
        )
    if account_id == payload.compte_reception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer to the same account",
        )

    account = await Compte.get_user_account(account_id, user)

    if account.solde < payload.montant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance"
        )

    compte_reception = await Compte.filter(id=payload.compte_reception).first()
    if not compte_reception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination account not found",
        )

    operation = await Virement.create(
        compte_envoi=account,
        compte_reception=compte_reception,
        montant=payload.montant,
    )

    return operation



@router.get(f"/tovalidate")
async def list_operations_to_validate(user: CurrentUser):
    user.can_authorize()
    virements = await Virement.filter(decision=None)
    retraits = await Retrait.filter(decision=None)
    return [virements, retraits]
