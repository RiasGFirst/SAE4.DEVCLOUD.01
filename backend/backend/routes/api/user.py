from fastapi import APIRouter, HTTPException, status
import pydantic

from backend.models import TypeUtilisateur, Utilisateur
from backend.auth import CurrentUser

from tortoise.exceptions import IntegrityError
from tortoise.contrib.pydantic import pydantic_model_creator

router = APIRouter()

@router.get("/", response_model=list[pydantic_model_creator(Utilisateur)])
async def list_users():
    """Liste tous les comptes utilisateurs créés."""
    users = await Utilisateur.all()
    return users


class CreateUserPayload(pydantic.BaseModel):
    """Payload pour la création d'un compte utilisateur."""
    nom: str
    email: str
    mot_de_passe: str
    role: TypeUtilisateur


@router.post("/", response_model=pydantic_model_creator(Utilisateur))
async def create_user(payload: CreateUserPayload):
    """Crée un nouveeau compte utilisateur en fonction des paramètres donnés."""
    try:
        user = await Utilisateur.create(
            nom=payload.nom,
            email=payload.email,
            password=payload.mot_de_passe,
            role=payload.role
        )
        return user
    except IntegrityError:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User already exists"
        )


@router.get("/me", response_model=pydantic_model_creator(Utilisateur))
async def get_user(user: CurrentUser):
    return user
