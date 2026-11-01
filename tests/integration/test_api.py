from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient


def create_customer(client: TestClient, headers: dict, payload: dict) -> dict:
    response = client.post("/api/v1/customers", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def create_catalog(client: TestClient, headers: dict) -> tuple[dict, dict]:
    service = client.post(
        "/api/v1/services",
        headers=headers,
        json={
            "name": "Troca de oleo",
            "description": "Troca completa",
            "price": "150.00",
            "estimated_minutes": 40,
        },
    )
    assert service.status_code == 201, service.text
    part = client.post(
        "/api/v1/parts",
        headers=headers,
        json={
            "name": "Filtro de oleo",
            "sku": "flt-001",
            "unit_price": "25.00",
            "stock_quantity": 10,
        },
    )
    assert part.status_code == 201, part.text
    return service.json(), part.json()


def create_order(
    client: TestClient, headers: dict, customer: dict, service: dict, part: dict
) -> dict:
    response = client.post(
        "/api/v1/work-orders",
        headers=headers,
        json={
            "customer_document": customer["document"],
            "vehicle": {
                "plate": "ABC1D23",
                "brand": "Honda",
                "model": "Civic",
                "year": 2022,
            },
            "services": [{"id": service["id"], "quantity": 1}],
            "parts": [{"id": part["id"], "quantity": 2}],
            "notes": "Cliente aguarda retorno",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_authentication_is_required_and_login_rejects_bad_password(client: TestClient):
    assert client.get("/api/v1/customers").status_code == 401
    assert (
        client.get("/api/v1/customers", headers={"Authorization": "Bearer invalid"}).status_code
        == 401
    )
    response = client.post("/api/v1/auth/token", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_customer_and_vehicle_crud(client: TestClient, auth_headers: dict, customer_payload: dict):
    customer = create_customer(client, auth_headers, customer_payload)
    duplicate = client.post("/api/v1/customers", json=customer_payload, headers=auth_headers)
    assert duplicate.status_code == 409
    listed = client.get("/api/v1/customers", headers=auth_headers).json()
    assert listed[0]["id"] == customer["id"]
    updated = client.patch(
        f"/api/v1/customers/{customer['id']}",
        headers=auth_headers,
        json={"phone": "11888888888"},
    )
    assert updated.status_code == 200
    assert updated.json()["phone"] == "11888888888"

    vehicle_response = client.post(
        "/api/v1/vehicles",
        headers=auth_headers,
        json={
            "customer_id": customer["id"],
            "plate": "ABC-1234",
            "brand": "Ford",
            "model": "Ka",
            "year": 2020,
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()
    assert vehicle["plate"] == "ABC1234"
    assert (
        client.get(f"/api/v1/vehicles?customer_id={customer['id']}", headers=auth_headers).json()[
            0
        ]["id"]
        == vehicle["id"]
    )
    patched = client.patch(
        f"/api/v1/vehicles/{vehicle['id']}", headers=auth_headers, json={"model": "Ka SE"}
    )
    assert patched.json()["model"] == "Ka SE"
    assert (
        client.delete(f"/api/v1/vehicles/{vehicle['id']}", headers=auth_headers).status_code == 204
    )
    assert (
        client.delete(f"/api/v1/customers/{customer['id']}", headers=auth_headers).status_code
        == 204
    )


def test_catalog_stock_and_soft_delete(client: TestClient, auth_headers: dict):
    service, part = create_catalog(client, auth_headers)
    updated_service = client.patch(
        f"/api/v1/services/{service['id']}", headers=auth_headers, json={"price": "175.50"}
    )
    assert Decimal(updated_service.json()["price"]) == Decimal("175.50")
    adjusted = client.post(
        f"/api/v1/parts/{part['id']}/stock-adjustments",
        headers=auth_headers,
        json={"quantity_delta": -3, "reason": "Inventario"},
    )
    assert adjusted.json()["stock_quantity"] == 7
    insufficient = client.post(
        f"/api/v1/parts/{part['id']}/stock-adjustments",
        headers=auth_headers,
        json={"quantity_delta": -100, "reason": "Erro"},
    )
    assert insufficient.status_code == 409
    client.delete(f"/api/v1/services/{service['id']}", headers=auth_headers)
    client.delete(f"/api/v1/parts/{part['id']}", headers=auth_headers)
    assert client.get("/api/v1/services", headers=auth_headers).json() == []
    assert client.get("/api/v1/parts", headers=auth_headers).json() == []
    assert (
        len(client.get("/api/v1/services?include_inactive=true", headers=auth_headers).json()) == 1
    )


def test_complete_work_order_flow_and_metrics(
    client: TestClient, auth_headers: dict, customer_payload: dict
):
    customer = create_customer(client, auth_headers, customer_payload)
    service, part = create_catalog(client, auth_headers)
    order = create_order(client, auth_headers, customer, service, part)
    assert order["status"] == "RECEBIDA"
    assert Decimal(order["quote_total"]) == Decimal("200.00")

    order_id = order["id"]
    diagnosis = client.post(f"/api/v1/work-orders/{order_id}/diagnosis", headers=auth_headers)
    assert diagnosis.json()["status"] == "EM_DIAGNOSTICO"
    quote = client.post(f"/api/v1/work-orders/{order_id}/quote", headers=auth_headers)
    assert quote.json()["status"] == "AGUARDANDO_APROVACAO"
    assert quote.json()["quote_status"] == "PENDENTE"

    public = client.get(
        f"/api/v1/public/work-orders/{order['tracking_code']}",
        params={"document": customer_payload["document"]},
    )
    assert public.status_code == 200
    wrong_document = client.get(
        f"/api/v1/public/work-orders/{order['tracking_code']}",
        params={"document": "11222333000181"},
    )
    assert wrong_document.status_code == 404

    approved = client.post(
        f"/api/v1/public/work-orders/{order['tracking_code']}/quote-decision",
        json={"document": customer_payload["document"], "approved": True},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "EM_EXECUCAO"
    assert (
        client.get(f"/api/v1/parts/{part['id']}", headers=auth_headers).json()["stock_quantity"]
        == 8
    )

    finalized = client.post(f"/api/v1/work-orders/{order_id}/finish", headers=auth_headers)
    assert finalized.json()["status"] == "FINALIZADA"
    delivered = client.post(f"/api/v1/work-orders/{order_id}/deliver", headers=auth_headers)
    assert delivered.json()["status"] == "ENTREGUE"
    metric = client.get("/api/v1/metrics/average-execution-time", headers=auth_headers).json()
    assert metric["completed_orders"] == 1
    assert metric["average_minutes"] >= 0
    assert len(client.get("/api/v1/work-orders", headers=auth_headers).json()) == 1
    assert (
        client.delete(f"/api/v1/customers/{customer['id']}", headers=auth_headers).status_code
        == 409
    )


def test_rejected_quote_can_be_revised(
    client: TestClient, auth_headers: dict, customer_payload: dict
):
    customer = create_customer(client, auth_headers, customer_payload)
    service, part = create_catalog(client, auth_headers)
    order = create_order(client, auth_headers, customer, service, part)
    client.post(f"/api/v1/work-orders/{order['id']}/diagnosis", headers=auth_headers)
    client.post(f"/api/v1/work-orders/{order['id']}/quote", headers=auth_headers)
    rejected = client.post(
        f"/api/v1/public/work-orders/{order['tracking_code']}/quote-decision",
        json={"document": customer_payload["document"], "approved": False},
    )
    assert rejected.json()["quote_status"] == "REJEITADO"
    assert (
        client.get(f"/api/v1/parts/{part['id']}", headers=auth_headers).json()["stock_quantity"]
        == 10
    )
    revised = client.put(
        f"/api/v1/work-orders/{order['id']}/items",
        headers=auth_headers,
        json={"services": [{"id": service["id"], "quantity": 2}], "parts": []},
    )
    assert revised.status_code == 200, revised.text
    assert revised.json()["status"] == "EM_DIAGNOSTICO"
    assert revised.json()["quote_total"] == "300.00"


def test_insufficient_stock_prevents_approval_and_invalid_transition_returns_conflict(
    client: TestClient, auth_headers: dict, customer_payload: dict
):
    customer = create_customer(client, auth_headers, customer_payload)
    service, part = create_catalog(client, auth_headers)
    order = create_order(client, auth_headers, customer, service, part)
    invalid = client.post(f"/api/v1/work-orders/{order['id']}/finish", headers=auth_headers)
    assert invalid.status_code == 409
    client.post(f"/api/v1/work-orders/{order['id']}/diagnosis", headers=auth_headers)
    client.post(f"/api/v1/work-orders/{order['id']}/quote", headers=auth_headers)
    client.post(
        f"/api/v1/parts/{part['id']}/stock-adjustments",
        headers=auth_headers,
        json={"quantity_delta": -10, "reason": "Consumo externo"},
    )
    approval = client.post(
        f"/api/v1/public/work-orders/{order['tracking_code']}/quote-decision",
        json={"document": customer_payload["document"], "approved": True},
    )
    assert approval.status_code == 409
    detail = client.get(f"/api/v1/work-orders/{order['id']}", headers=auth_headers).json()
    assert detail["status"] == "AGUARDANDO_APROVACAO"
