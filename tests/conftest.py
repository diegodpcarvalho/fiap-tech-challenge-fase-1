from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret-with-at-least-thirty-two-characters"  # noqa: S105
os.environ["ADMIN_USERNAME"] = "admin"

from garage.infrastructure.security import hash_password  # noqa: E402

os.environ["ADMIN_PASSWORD_HASH"] = hash_password("Admin12345!", salt=b"0123456789abcdef")

from garage.infrastructure.database import Base, engine  # noqa: E402
from garage.main import app  # noqa: E402


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/token", json={"username": "admin", "password": "Admin12345!"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def customer_payload() -> dict[str, str]:
    return {
        "name": "Maria da Silva",
        "document": "529.982.247-25",
        "email": "maria@example.com",
        "phone": "11999999999",
    }
