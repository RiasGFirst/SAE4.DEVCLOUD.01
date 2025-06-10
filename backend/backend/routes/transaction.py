from decimal import Decimal
from typing import Annotated

import pydantic
from fastapi import APIRouter, HTTPException, status
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.transactions import in_transaction

from backend.auth import CurrentUser
from backend.models import Compte, Decision, Operation, TypeOperation

router = APIRouter()


class CreateOperationOnlyAmountPayload(pydantic.BaseModel):
    """Payload pour la création d'une opération."""

    montant: float


@router.post(
    "/{account_id}/depot",
    response_model=Annotated[Operation, pydantic_model_creator(Operation)],
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
    await account.ensure_validated()

    if payload.montant <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive"
        )

    async with in_transaction():
        operation = await Operation.create(
            type_operation=TypeOperation.DEPOT,
            compte_source=None,
            compte_destination=account,
            montant=payload.montant,
        )
        await Decision.create(operation=operation, valide=True, agent=None)
        operation.processed = True
        await operation.save()

        account.solde += Decimal(payload.montant)
        await account.save()

        return operation


@router.post(
    "/{account_id}/retrait",
    response_model=Annotated[Operation, pydantic_model_creator(Operation)],
)
async def create_withdrawal_operation(
    account_id: int, user: CurrentUser, payload: CreateOperationOnlyAmountPayload
):
    if payload.montant <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive"
        )

    account = await Compte.get_user_account(account_id, user)
    await account.ensure_validated()

    if account.solde < payload.montant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance"
        )

    async with in_transaction():
        operation = await Operation.create(
            type_operation=TypeOperation.RETRAIT,
            compte_source=account,
            compte_destination=None,
            montant=-payload.montant,
        )
        account.solde -= Decimal(payload.montant)
        return operation


class CreateOperationVirementPayload(pydantic.BaseModel):
    """Payload pour la création d'une opération vers un compte."""

    target: int
    montant: float


@router.post(
    "/{account_id}/virement",
    response_model=Annotated[Operation, pydantic_model_creator(Operation)],
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
    if account_id == payload.target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer to the same account",
        )

    account = await Compte.get_user_account(account_id, user)
    try:
        await account.ensure_validated()
    except HTTPException as exception:
        exception.detail += " (Account: source)"
        raise exception

    if account.solde < payload.montant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance"
        )

    compte_reception = await Compte.filter(id=payload.target).first()
    if not compte_reception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination account not found",
        )
    try:
        await compte_reception.ensure_validated()
    except HTTPException as exception:
        exception.detail += " (Account: destination)"
        raise exception

    async with in_transaction():
        operation = await Operation.create(
            type_operation=TypeOperation.VIREMENT,
            compte_source=account,
            compte_destination=compte_reception,
            montant=-payload.montant,
        )

    return operation


@router.get("/tovalidate", response_model=list[pydantic_model_creator(Operation)])
@router.get("/tovalidate")
async def list_operations_to_validate(user: CurrentUser):
    user.can_authorize()
    virements = await Operation.filter(decision=None).prefetch_related(
        "compte_source", "compte_destination"
    )
    return [virement.__dict__ for virement in virements]


class AuthorizeOperationPayload(pydantic.BaseModel):
    authorize: bool


@router.post("/validate/{id}")
async def validate_operation(
    id: int, payload: AuthorizeOperationPayload, user: CurrentUser
):
    user.can_authorize()

    operation = await Operation.get_or_none(id=id).prefetch_related("decision")
    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operation not found",
        )
    if operation.decision:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operation already validated",
        )

    async with in_transaction():
        await Decision.create(operation=operation, valide=payload.authorize, agent=user)
        operation.processed = True
        await operation.save()

    return operation
