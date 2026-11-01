from __future__ import annotations

import os
import secrets
from pathlib import Path

from garage.infrastructure.security import hash_password

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
CREDENTIAL_FILE = PROJECT_ROOT / ".demo-credentials"


def main() -> None:
    if ENV_FILE.exists() or CREDENTIAL_FILE.exists():
        raise SystemExit(
            "Ambiente local ja configurado. Remova manualmente .env e "
            ".demo-credentials somente se quiser gerar novas credenciais."
        )

    admin_password = secrets.token_urlsafe(18)
    postgres_password = secrets.token_urlsafe(24)
    jwt_secret = secrets.token_urlsafe(48)
    admin_hash = hash_password(admin_password)

    ENV_FILE.write_text(
        "\n".join(
            [
                "ENVIRONMENT=development",
                "APP_NAME='Oficina API'",
                f"POSTGRES_PASSWORD='{postgres_password}'",
                f"JWT_SECRET='{jwt_secret}'",
                "ACCESS_TOKEN_MINUTES=30",
                "ADMIN_USERNAME=admin",
                f"ADMIN_PASSWORD_HASH='{admin_hash}'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    CREDENTIAL_FILE.write_text(
        "\n".join(
            [
                "CREDENCIAL LOCAL DE DEMONSTRACAO - NAO ENVIAR AO GIT",
                "Usuario: admin",
                f"Senha: {admin_password}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    os.chmod(ENV_FILE, 0o600)
    os.chmod(CREDENTIAL_FILE, 0o600)
    print("Ambiente local criado sem exibir segredos.")
    print(f"Credencial administrativa salva somente em: {CREDENTIAL_FILE}")


if __name__ == "__main__":
    main()
