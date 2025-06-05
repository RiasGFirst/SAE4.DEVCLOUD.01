from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from backend.models import Utilisateur

scheme = HTTPBasic()


async def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(scheme)],
) -> Utilisateur:
    user = await Utilisateur.get_or_none(email=credentials.username)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if not user.verify_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mot de passe incorrect",
        )
    return user


CurrentUser = Annotated[Utilisateur, Depends(get_current_user)]
