from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    environment: str
    database_url: str
    jwt_secret: str
    jwt_algorithm: str
    access_token_minutes: int
    admin_username: str
    admin_password_hash: str

    @classmethod
    def from_environment(cls) -> Settings:
        settings = cls(
            app_name=os.getenv("APP_NAME", "Oficina API"),
            environment=os.getenv("ENVIRONMENT", "development"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./garage.db"),
            jwt_secret=os.getenv("JWT_SECRET", ""),
            jwt_algorithm="HS256",
            access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "30")),
            admin_username=os.getenv("ADMIN_USERNAME", "admin"),
            admin_password_hash=os.getenv("ADMIN_PASSWORD_HASH", ""),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if len(self.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET deve possuir pelo menos 32 caracteres.")
        if not self.admin_password_hash:
            raise RuntimeError("ADMIN_PASSWORD_HASH precisa ser configurado.")


@lru_cache
def get_settings() -> Settings:
    return Settings.from_environment()
