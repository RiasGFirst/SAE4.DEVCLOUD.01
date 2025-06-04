from typing import Annotated

from passlib.hash import argon2
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from backend.models import Utilisateur

scheme = HTTPBasic()


def verify_password(user: Utilisateur, password: str) -> bool:
    """Vérifie si le mot de passe en clair correspond au mot de passe haché."""
    return argon2.verify(password, user.password)


async def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(scheme)],
) -> Utilisateur:
    user = await Utilisateur.get_or_none(
        email=credentials.username
    )
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if not user.password == credentials.password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mot de passe incorrect",
        )
    return user


CurrentUser = Annotated[Utilisateur, Depends(get_current_user)]
