from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from garage.application.services import GarageApplication
from garage.config import Settings, get_settings
from garage.infrastructure.database import get_db
from garage.infrastructure.security import decode_access_token

bearer = HTTPBearer(auto_error=False)

Database = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_application(database: Database) -> GarageApplication:
    return GarageApplication(database)


Application = Annotated[GarageApplication, Depends(get_application)]


def require_admin(
    application: Application,
    settings: AppSettings,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials or credentials.scheme.lower() != "bearer":
        raise unauthorized
    username = decode_access_token(credentials.credentials, settings)
    if not username or not application.authenticate(username):
        raise unauthorized
    return username


AdminUser = Annotated[str, Depends(require_admin)]
