import typing
from enum import Enum

from fastapi import HTTPException
from passlib.hash import sha256_crypt
from tortoise import BaseDBAsyncClient, Model, fields
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.signals import pre_save


class TypeUtilisateur(str, Enum):
    USER = "utilisateur"
    AGENT = "agent_bancaire"


class RequireValidation:
    validated = fields.BooleanField(default=False)


class Utilisateur(Model):
    id = fields.IntField(primary_key=True, unique=True)
    nom = fields.CharField(max_length=100)
    email = fields.CharField(max_length=255, unique=True)
    password = fields.CharField(max_length=255)
    role = fields.CharEnumField(TypeUtilisateur, default=TypeUtilisateur.USER)
    date_creation = fields.DatetimeField(auto_now_add=True)

    comptes = fields.ReverseRelation["Compte"]

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


class Compte(Model, RequireValidation):
    id = fields.IntField(primary_key=True, unique=True)
    utilisateur: fields.ForeignKeyRelation["Utilisateur"] = fields.ForeignKeyField(
        "models.Utilisateur", related_name="comptes"
    )
    type_compte = fields.CharEnumField(TypeCompte)
    solde = fields.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    date_creation = fields.DatetimeField(auto_now_add=True)

    retraits = fields.ReverseRelation["Retrait"]
    depots = fields.ReverseRelation["Depot"]
    operations_envoi = fields.ReverseRelation["Virement"]
    operations_reception = fields.ReverseRelation["Virement"]

    def ensure_validated(self) -> typing.Literal[True]:
        if not self.validated:
            raise HTTPException(status_code=403, detail="Account not yet validated.")
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

    async def get_all_operations(self) -> list["Retrait | Depot | Virement"]:
        return [
            *(await Retrait.filter(compte=self)),
            *(await Depot.filter(compte=self)),
            *(await Virement.filter(compte_envoi=self)),
        ]


class Retrait(Model):
    operation = "retrait"

    id = fields.IntField(primary_key=True, unique=True)
    compte: fields.ForeignKeyRelation["Compte"] = fields.ForeignKeyField(
        "models.Compte", related_name="retraits"
    )
    montant = fields.DecimalField(max_digits=15, decimal_places=2)
    date_creation = fields.DatetimeField(auto_now_add=True)

    decision = fields.ForeignKeyField(
        "models.Decision", related_name="retraits", null=True, on_delete=fields.RESTRICT
    )

    class PydanticMeta:
        extra = ["operation"]

    async def get_decision(self) -> "Decision | None":
        return await Decision.filter(operation=self).first()


RetraitPydantic = typing.Annotated[Retrait, pydantic_model_creator(Retrait, name="Retrait")]


class Depot(Model):
    operation = "depot"

    id = fields.IntField(primary_key=True, unique=True)
    compte: fields.ForeignKeyNullableRelation["Compte"] = fields.ForeignKeyField(
        "models.Compte", related_name="depots"
    )
    montant = fields.DecimalField(max_digits=15, decimal_places=2)
    date_creation = fields.DatetimeField(auto_now_add=True)


DepotPydantic = typing.Annotated[Depot, pydantic_model_creator(Depot, name="Depot")]


class Virement(Model):
    operation = "virement"

    id = fields.IntField(primary_key=True, unique=True)
    compte_envoi: fields.ForeignKeyNullableRelation["Compte"] = fields.ForeignKeyField(
        "models.Compte", related_name="operations_envoi", null=True
    )
    compte_reception: fields.ForeignKeyRelation["Compte"] = fields.ForeignKeyField(
        "models.Compte", related_name="operations_reception"
    )
    montant = fields.DecimalField(max_digits=15, decimal_places=2)
    date_creation = fields.DatetimeField(auto_now_add=True)

    decision = fields.ForeignKeyField(
        "models.Decision",
        related_name="virements",
        null=True,
        on_delete=fields.RESTRICT,
    )

    async def get_decision(self) -> "Decision | None":
        return await Decision.filter(operation=self).first()


VirementPydantic = typing.Annotated[Virement, pydantic_model_creator(Virement, name="Virement")]


Operations: typing.TypeAlias = "type[Retrait | Depot | Virement]"

class Decision(Model):
    id = fields.IntField(primary_key=True, unique=True)
    valide = fields.BooleanField(null=True, default=None)
    agent = fields.ForeignKeyField(
        "models.Utilisateur",
        related_name="decisions_agent",
        null=True,
        on_delete=fields.CASCADE,
    )
    date_creation = fields.DatetimeField(auto_now_add=True)

    depots: fields.ReverseRelation["Depot"]
    retraits: fields.ReverseRelation["Depot"]
    virements: fields.ReverseRelation["Virement"]


class Log(Model):
    id = fields.IntField(primary_key=True, unique=True)
    ip = fields.CharField(max_length=255, null=True)
    chemin = fields.TextField()
    code_reponse = fields.IntField()
    date_creation = fields.DatetimeField(auto_now_add=True)
