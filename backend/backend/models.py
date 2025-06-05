from enum import Enum

from fastapi import HTTPException
from passlib.hash import sha256_crypt
from tortoise import BaseDBAsyncClient, Model, fields
from tortoise.expressions import Q
from tortoise.signals import pre_save


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

    def verify_password(self, password: str) -> bool:
        """
        Vérifie si le mot de passe en clair correspond au mot de passe haché.
        """
        return sha256_crypt.verify(password, self.password)

    class PydanticMeta:
        exclude = ["password"]


@pre_save(Utilisateur)
async def user_hash_password(
    sender: type[Utilisateur],
    instance: Utilisateur,
    using_db: BaseDBAsyncClient | None,
    update_fields: list[str],
) -> None:
    """
    Vérifixe que l'utilisateur a un mot de passe avant de sauvegarder.
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
    utilisateur: fields.ForeignKeyRelation["Utilisateur"] = fields.ForeignKeyField(
        "models.Utilisateur", related_name="comptes"
    )
    type_compte = fields.CharEnumField(TypeCompte)
    solde = fields.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date_creation = fields.DatetimeField(auto_now_add=True)

    @classmethod
    async def get_user_account(cls, account_id: int, user: "Utilisateur") -> "Compte":
        """
        Essaye de trouver un compte pour un utilisateur et l'identifiant de son compte.
        """
        found_account = await cls.filter(utilisateur=user, id=account_id).first()
        if not found_account:
            raise HTTPException(status_code=404, detail="Account not found.")
        return found_account

    async def get_operations(self) -> list["Operation"]:
        """
        Récupère toutes les opérations associées à ce compte.
        """
        return await Operation.filter(Q(compte_envoi=self) | Q(compte_reception=self))


class Operation(Model):
    id = fields.IntField(primary_key=True, unique=True)
    compte_envoi: fields.ForeignKeyRelation["Compte"] = fields.ForeignKeyField(
        "models.Compte", related_name="operations_envoi"
    )
    compte_reception: fields.ForeignKeyRelation["Compte"] = fields.ForeignKeyField(
        "models.Compte", related_name="operations_reception"
    )
    montant = fields.DecimalField(max_digits=15, decimal_places=2)
    date_creation = fields.DatetimeField(auto_now_add=True)

    decision = fields.ReverseRelation["Decision"]


class Decision(Model):
    operation: fields.ForeignKeyRelation["Operation"] = fields.ForeignKeyField(
        "models.Operation", related_name="decision", primary_key=True, unique=True
    )
    valide = fields.BooleanField()
    agent = fields.ForeignKeyField("models.Utilisateur", related_name="decisions_agent")
    date_creation = fields.DatetimeField(auto_now_add=True)


class LogAction(str, Enum):
    VALID = "valide"
    INVALID = "invalide"


class Log(Model):
    id = fields.IntField(primary_key=True, unique=True)
    utilisateur: fields.ForeignKeyNullableRelation["Utilisateur"] = (
        fields.ForeignKeyField(
            "models.Utilisateur",
            related_name="logs",
            null=True,
            on_delete=fields.SET_NULL,
        )
    )
    chemin = fields.TextField()
    date_creation = fields.DatetimeField(auto_now_add=True)
