import typing
from enum import Enum
from functools import partial

from fastapi import HTTPException
from passlib.hash import sha256_crypt
from schwifty import IBAN
from tortoise import BaseDBAsyncClient, Model, fields
from tortoise.expressions import Q
from tortoise.signals import post_save, pre_save
from tortoise.transactions import in_transaction


class TypeUtilisateur(str, Enum):
    USER = "utilisateur"
    AGENT = "agent_bancaire"


class Utilisateur(Model):
    id = fields.IntField(primary_key=True, unique=True)
    nom = fields.CharField(max_length=100)
    email = fields.CharField(max_length=255, unique=True)
    password = fields.CharField(max_length=255)
    role = fields.CharEnumField(TypeUtilisateur, default=TypeUtilisateur.USER)
    date_creation = fields.DatetimeField(auto_now_add=True)

    comptes: fields.ReverseRelation["Compte"]

    def verify_password(self, password: str) -> bool:
        """
        Vérifie si le mot de passe en clair correspond au mot de passe haché.
        """
        return sha256_crypt.verify(password, self.password)

    class PydanticMeta:
        exclude = ["password"]

    def can_authorize(self) -> typing.Literal[True]:
        """
        Vérifie si l'utilisateur a le droit de valider les comptes.
        """
        if not self.role == TypeUtilisateur.AGENT:
            raise HTTPException(status_code=403, detail="Missing privileges.")
        return True


@pre_save(Utilisateur)
async def user_hash_password(
    sender: type[Utilisateur],
    instance: Utilisateur,
    using_db: BaseDBAsyncClient | None,
    update_fields: list[str],
) -> None:
    """
    Vérifie que l'utilisateur a un mot de passe avant de sauvegarder.
    Sinon, hasher le mot de passe si nécessaire.
    """
    if not instance.password:
        raise ValueError("Le mot de passe ne peut pas être vide.")
    if not instance.password.startswith("$5$"):
        instance.password = sha256_crypt.hash(instance.password)


class TypeCompte(str, Enum):
    COURANT = "compte_courant"
    LIVRET = "livret"


class Compte(Model):
    id = fields.IntField(primary_key=True, unique=True)
    iban = fields.CharField(
        max_length=34, unique=True, default=partial(IBAN.random, country_code="FR")
    )
    utilisateur: fields.ForeignKeyRelation["Utilisateur"] = fields.ForeignKeyField(
        "models.Utilisateur", related_name="comptes"
    )
    type_compte = fields.CharEnumField(TypeCompte)
    solde = fields.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    validation: fields.ReverseRelation["ValidationCompte"]

    date_creation = fields.DatetimeField(auto_now_add=True)

    async def ensure_validated(self) -> typing.Literal[True]:
        validation = await ValidationCompte.filter(compte=self).get_or_none()
        if not validation:
            raise HTTPException(status_code=403, detail="Account not yet validated.")
        if not validation.valide:
            raise HTTPException(status_code=403, detail="Account not validated.")
        return True

    @classmethod
    async def get_user_account(cls, account_id: int, user: "Utilisateur") -> "Compte":
        """
        Essaye de trouver un compte pour un utilisateur et l'identifiant de son compte.
        """
        found_account = await cls.filter(utilisateur=user, id=account_id).first()
        if not found_account:
            raise HTTPException(status_code=404, detail="Account not found.")
        return found_account

    async def get_all_operations(
        self, prefetch_decisions: bool = False
    ) -> typing.Iterable["Operation"]:
        return await Operation.filter_by_account(self, prefetch_decisions)


class ValidationCompte(Model):
    """Modèle utilisé pour confirmer qu'un compte peut être utilisé."""

    id = fields.IntField(primary_key=True, unique=True)
    valide = fields.BooleanField(default=False)
    compte: fields.ForeignKeyRelation["Compte"] = fields.ForeignKeyField(
        "models.Compte", related_name="validation"
    )
    agent: fields.ForeignKeyNullableRelation["Utilisateur"] = fields.ForeignKeyField(
        "models.Utilisateur", related_name="validation_agent", null=True
    )
    date_validation = fields.DatetimeField(auto_now_add=True)


class TypeOperation(str, Enum):
    DEPOT = "depot"
    RETRAIT = "retrait"
    VIREMENT = "virement"


class Operation(Model):
    id = fields.IntField(primary_key=True, unique=True)
    type_operation = fields.CharEnumField(TypeOperation)

    compte_source: fields.ForeignKeyNullableRelation["Compte"] = fields.ForeignKeyField(
        "models.Compte", related_name="operations_source", null=True
    )
    compte_destination: fields.ForeignKeyNullableRelation["Compte"] = (
        fields.ForeignKeyField(
            "models.Compte", related_name="operations_destination", null=True
        )
    )

    processed = fields.BooleanField(default=False)
    montant = fields.DecimalField(max_digits=16, decimal_places=2)
    decision = fields.ForeignKeyNullableRelation["Decision"]

    date_creation = fields.DatetimeField(auto_now_add=True)

    @classmethod
    async def filter_unvalidated(cls) -> typing.Iterable[typing.Self]:
        return await cls.filter(decision=None)

    @classmethod
    def filter_by_account(cls, compte: "Compte", prefetch_decisions: bool = False):
        op = cls.filter(Q(compte_source=compte) | Q(compte_destination=compte))
        if prefetch_decisions:
            return op.prefetch_related("decision")
        return op


class Decision(Model):
    id = fields.IntField(primary_key=True, unique=True)
    valide = fields.BooleanField(null=True, default=None)
    agent = fields.ForeignKeyField(
        "models.Utilisateur",
        related_name="decisions_agent",
        null=True,
        on_delete=fields.RESTRICT,
    )
    operation: fields.ForeignKeyRelation["Operation"] = fields.ForeignKeyField(
        "models.Operation", related_name="decision"
    )
    date_creation = fields.DatetimeField(auto_now_add=True)


@post_save(Decision)
async def update_operation(
    sender: type[Decision],
    instance: Decision,
    created: bool,
    using_db: BaseDBAsyncClient | None,
    update_fields: list[str],
) -> None:
    if not instance.operation:
        await instance.fetch_related("operation")

    if instance.operation.type_operation == TypeOperation.DEPOT or not instance.valide:
        return

    await instance.operation.fetch_related("compte_source", "compte_destination")
    source = instance.operation.compte_source
    destination = instance.operation.compte_destination

    async with in_transaction():
        if source:
            source.solde += instance.operation.montant
            await source.save()
        if destination:
            destination.solde -= instance.operation.montant
            await destination.save()


class Log(Model):
    id = fields.IntField(primary_key=True, unique=True)
    ip = fields.CharField(max_length=255, null=True)
    chemin = fields.TextField()
    code_reponse = fields.IntField()
    date_creation = fields.DatetimeField(auto_now_add=True)
