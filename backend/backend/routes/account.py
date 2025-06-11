from typing import Annotated

import pydantic
from fastapi import APIRouter, HTTPException, Response, status
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import IntegrityError

from backend.auth import CurrentUser
from backend.models import Compte, Operation, TypeCompte, ValidationCompte

router = APIRouter()


class ListAccountsResponse(pydantic.BaseModel):
    account: Annotated[Compte, pydantic_model_creator(Compte)]
    validation: (
        Annotated[ValidationCompte, pydantic_model_creator(ValidationCompte)] | None
    )


@router.get("", response_model=list[ListAccountsResponse])
async def list_accounts(user: CurrentUser):
    """Liste tous les comptes utilisateurs créés."""
    accounts = await Compte.filter(utilisateur=user)
    accounts_ids = [str(account.id) for account in accounts]
    validations = await ValidationCompte.in_bulk(accounts_ids, field_name="compte_id")

    return [
        ListAccountsResponse(
            account=account,
            validation=validations.get(
                account.id  # pyright: ignore[reportArgumentType]
            ),
        )
        for account in accounts
    ]


@router.get("/tovalidate", response_model=list[pydantic_model_creator(Compte)])
async def list_accounts_to_validate(user: CurrentUser):
    """Liste tous les comptes utilisateurs à valider."""
    user.can_authorize()
    accounts = await Compte.filter(validation=None)
    return accounts


class CreateAccountPayload(pydantic.BaseModel):
    """Payload pour la création d'un compte."""

    type: TypeCompte
    solde_initial: float = 0.0


@router.post("", response_model=pydantic_model_creator(Compte))
async def create_account(user: CurrentUser, payload: CreateAccountPayload):
    """Crée un nouveeau compte en fonction des paramètres donnés.

    Le type de compte permet de savoir si nous créons un compte courant, ou un livret.

    Demander l'ouverture d'un compte requiert la validation d'un agent bancaire.
    """
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
    validation: (
        Annotated[ValidationCompte, pydantic_model_creator(ValidationCompte)] | None
    )


@router.get("/{account_id}", response_model=GetAccountResponse)
async def get_account(account_id: int, user: CurrentUser):
    """Récupère un compte utilisateur spécifique.

    Retourne une liste d'information avec le compte, ses opérations, et son status de validation.

    Si la validation est "null", la validation n'a pas encore eu lieu.
    """
    account = await Compte.get_user_account(account_id, user)
    validation = await ValidationCompte.filter(compte=account).get_or_none()

    return {
        "account": account,
        "operations": await account.get_all_operations(True),
        "validation": validation,
    }


class AuthorizeAccountPayload(pydantic.BaseModel):
    """Payload pour la validation d'un compte."""

    authorize: bool


@router.post("/{account_id}/approval")
async def authorize_account(
    account_id: int, user: CurrentUser, payload: AuthorizeAccountPayload
):
    user.can_authorize()

    account = await Compte.filter(id=account_id).get_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )

    await ValidationCompte.create(compte=account, valide=payload.authorize, agent=user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me", response_model=None)
async def delete_user(user: CurrentUser):
    """Supprime le compte utilisateur connecté."""
    await user.delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
