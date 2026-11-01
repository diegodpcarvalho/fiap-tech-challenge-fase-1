from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select

from garage.config import get_settings
from garage.domain.exceptions import ConflictError, DomainError, NotFoundError, ValidationError
from garage.infrastructure.database import SessionLocal, initialize_database
from garage.infrastructure.models import AdminUserModel
from garage.presentation.router import router


def _ensure_admin() -> None:
    settings = get_settings()
    with SessionLocal() as session:
        user = session.scalar(
            select(AdminUserModel).where(AdminUserModel.username == settings.admin_username)
        )
        if not user:
            session.add(
                AdminUserModel(
                    username=settings.admin_username,
                    password_hash=settings.admin_password_hash,
                    active=True,
                )
            )
            session.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    _ensure_admin()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "API do MVP da oficina. Rotas administrativas usam JWT; rotas publicas de "
            "acompanhamento usam codigo da OS e CPF/CNPJ enviado no corpo da requisicao."
        ),
        lifespan=lifespan,
    )
    application.include_router(router)

    @application.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        code = status.HTTP_400_BAD_REQUEST
        if isinstance(exc, NotFoundError):
            code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, ConflictError):
            code = status.HTTP_409_CONFLICT
        elif isinstance(exc, ValidationError):
            code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return JSONResponse(status_code=code, content={"detail": str(exc)})

    return application


app = create_app()
