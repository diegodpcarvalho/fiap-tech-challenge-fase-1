from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from garage.config import get_settings
from garage.domain.enums import WorkOrderStatus
from garage.infrastructure.security import create_access_token, verify_password
from garage.presentation.dependencies import AdminUser, Application
from garage.presentation.schemas import (
    AverageExecutionTime,
    CatalogServiceCreate,
    CatalogServiceRead,
    CatalogServiceUpdate,
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    HealthResponse,
    PartCreate,
    PartRead,
    PartUpdate,
    PublicWorkOrderRead,
    QuoteDecision,
    StockAdjustment,
    TokenRequest,
    TokenResponse,
    VehicleCreate,
    VehicleRead,
    VehicleUpdate,
    WorkOrderCreate,
    WorkOrderItemRead,
    WorkOrderItemsReplace,
    WorkOrderRead,
)

router = APIRouter(prefix="/api/v1")


def _dump(model, *, exclude_unset: bool = False) -> dict:
    return model.model_dump(exclude_unset=exclude_unset, exclude_none=exclude_unset)


def _work_order_response(model) -> WorkOrderRead:
    def item_response(item, reference_field: str) -> WorkOrderItemRead:
        unit_price = item.unit_price_snapshot
        return WorkOrderItemRead(
            reference_id=getattr(item, reference_field),
            description=item.description_snapshot,
            unit_price=unit_price,
            quantity=item.quantity,
            subtotal=Decimal(unit_price) * item.quantity,
        )

    return WorkOrderRead(
        id=model.id,
        tracking_code=model.tracking_code,
        customer_id=model.customer_id,
        vehicle_id=model.vehicle_id,
        vehicle_plate=model.vehicle.plate,
        notes=model.notes,
        status=model.status,
        quote_status=model.quote_status,
        quote_total=model.quote_total,
        services=[item_response(item, "service_id") for item in model.service_items],
        parts=[item_response(item, "part_id") for item in model.part_items],
        created_at=model.created_at,
        updated_at=model.updated_at,
        diagnosis_started_at=model.diagnosis_started_at,
        approved_at=model.approved_at,
        execution_started_at=model.execution_started_at,
        finalized_at=model.finalized_at,
        delivered_at=model.delivered_at,
    )


@router.get("/health", response_model=HealthResponse, tags=["Operacao"])
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/auth/token", response_model=TokenResponse, tags=["Autenticacao"])
def login(payload: TokenRequest, application: Application) -> TokenResponse:
    from fastapi import HTTPException

    user = application.authenticate(payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuario ou senha invalidos.")
    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(user.username, settings),
        expires_in=settings.access_token_minutes * 60,
    )


# Customers
@router.post(
    "/customers",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Clientes"],
)
def create_customer(payload: CustomerCreate, app: Application, _admin: AdminUser):
    return app.create_customer(_dump(payload))


@router.get("/customers", response_model=list[CustomerRead], tags=["Clientes"])
def list_customers(
    app: Application, _admin: AdminUser, offset: int = 0, limit: int = Query(100, le=200)
):
    return app.list_customers(offset, limit)


@router.get("/customers/{customer_id}", response_model=CustomerRead, tags=["Clientes"])
def get_customer(customer_id: str, app: Application, _admin: AdminUser):
    return app.get_customer(customer_id)


@router.patch("/customers/{customer_id}", response_model=CustomerRead, tags=["Clientes"])
def update_customer(customer_id: str, payload: CustomerUpdate, app: Application, _admin: AdminUser):
    return app.update_customer(customer_id, _dump(payload, exclude_unset=True))


@router.delete(
    "/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Clientes"]
)
def delete_customer(customer_id: str, app: Application, _admin: AdminUser) -> Response:
    app.delete_customer(customer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Vehicles
@router.post(
    "/vehicles", response_model=VehicleRead, status_code=status.HTTP_201_CREATED, tags=["Veiculos"]
)
def create_vehicle(payload: VehicleCreate, app: Application, _admin: AdminUser):
    return app.create_vehicle(_dump(payload))


@router.get("/vehicles", response_model=list[VehicleRead], tags=["Veiculos"])
def list_vehicles(
    app: Application,
    _admin: AdminUser,
    customer_id: str | None = None,
    offset: int = 0,
    limit: int = Query(100, le=200),
):
    return app.list_vehicles(customer_id, offset, limit)


@router.get("/vehicles/{vehicle_id}", response_model=VehicleRead, tags=["Veiculos"])
def get_vehicle(vehicle_id: str, app: Application, _admin: AdminUser):
    return app.get_vehicle(vehicle_id)


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleRead, tags=["Veiculos"])
def update_vehicle(vehicle_id: str, payload: VehicleUpdate, app: Application, _admin: AdminUser):
    return app.update_vehicle(vehicle_id, _dump(payload, exclude_unset=True))


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Veiculos"])
def delete_vehicle(vehicle_id: str, app: Application, _admin: AdminUser) -> Response:
    app.delete_vehicle(vehicle_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Service catalog
@router.post(
    "/services",
    response_model=CatalogServiceRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Servicos"],
)
def create_service(payload: CatalogServiceCreate, app: Application, _admin: AdminUser):
    return app.create_catalog_service(_dump(payload))


@router.get("/services", response_model=list[CatalogServiceRead], tags=["Servicos"])
def list_services(
    app: Application,
    _admin: AdminUser,
    include_inactive: bool = False,
    offset: int = 0,
    limit: int = Query(100, le=200),
):
    return app.list_catalog_services(include_inactive, offset, limit)


@router.get("/services/{service_id}", response_model=CatalogServiceRead, tags=["Servicos"])
def get_service(service_id: str, app: Application, _admin: AdminUser):
    return app.get_catalog_service(service_id)


@router.patch("/services/{service_id}", response_model=CatalogServiceRead, tags=["Servicos"])
def update_service(
    service_id: str, payload: CatalogServiceUpdate, app: Application, _admin: AdminUser
):
    return app.update_catalog_service(service_id, _dump(payload, exclude_unset=True))


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Servicos"])
def delete_service(service_id: str, app: Application, _admin: AdminUser) -> Response:
    app.delete_catalog_service(service_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Parts
@router.post(
    "/parts", response_model=PartRead, status_code=status.HTTP_201_CREATED, tags=["Pecas e estoque"]
)
def create_part(payload: PartCreate, app: Application, _admin: AdminUser):
    return app.create_part(_dump(payload))


@router.get("/parts", response_model=list[PartRead], tags=["Pecas e estoque"])
def list_parts(
    app: Application,
    _admin: AdminUser,
    include_inactive: bool = False,
    offset: int = 0,
    limit: int = Query(100, le=200),
):
    return app.list_parts(include_inactive, offset, limit)


@router.get("/parts/{part_id}", response_model=PartRead, tags=["Pecas e estoque"])
def get_part(part_id: str, app: Application, _admin: AdminUser):
    return app.get_part(part_id)


@router.patch("/parts/{part_id}", response_model=PartRead, tags=["Pecas e estoque"])
def update_part(part_id: str, payload: PartUpdate, app: Application, _admin: AdminUser):
    return app.update_part(part_id, _dump(payload, exclude_unset=True))


@router.post(
    "/parts/{part_id}/stock-adjustments",
    response_model=PartRead,
    tags=["Pecas e estoque"],
)
def adjust_stock(part_id: str, payload: StockAdjustment, app: Application, _admin: AdminUser):
    return app.adjust_stock(part_id, payload.quantity_delta, payload.reason)


@router.delete("/parts/{part_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Pecas e estoque"])
def delete_part(part_id: str, app: Application, _admin: AdminUser) -> Response:
    app.delete_part(part_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Work orders - administrative
@router.post(
    "/work-orders",
    response_model=WorkOrderRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Ordens de servico"],
)
def create_work_order(payload: WorkOrderCreate, app: Application, _admin: AdminUser):
    data = _dump(payload)
    return _work_order_response(app.create_work_order(data))


@router.get("/work-orders", response_model=list[WorkOrderRead], tags=["Ordens de servico"])
def list_work_orders(
    app: Application,
    _admin: AdminUser,
    order_status: Annotated[WorkOrderStatus | None, Query(alias="status")] = None,
    offset: int = 0,
    limit: int = Query(100, le=200),
):
    return [
        _work_order_response(item) for item in app.list_work_orders(order_status, offset, limit)
    ]


@router.get(
    "/work-orders/{work_order_id}",
    response_model=WorkOrderRead,
    tags=["Ordens de servico"],
)
def get_work_order(work_order_id: str, app: Application, _admin: AdminUser):
    return _work_order_response(app.get_work_order(work_order_id))


@router.put(
    "/work-orders/{work_order_id}/items", response_model=WorkOrderRead, tags=["Ordens de servico"]
)
def replace_work_order_items(
    work_order_id: str, payload: WorkOrderItemsReplace, app: Application, _admin: AdminUser
):
    return _work_order_response(
        app.replace_work_order_items(
            work_order_id,
            [_dump(item) for item in payload.services],
            [_dump(item) for item in payload.parts],
        )
    )


@router.post(
    "/work-orders/{work_order_id}/diagnosis",
    response_model=WorkOrderRead,
    tags=["Ordens de servico"],
)
def start_diagnosis(work_order_id: str, app: Application, _admin: AdminUser):
    return _work_order_response(app.start_diagnosis(work_order_id))


@router.post(
    "/work-orders/{work_order_id}/quote", response_model=WorkOrderRead, tags=["Ordens de servico"]
)
def send_quote(work_order_id: str, app: Application, _admin: AdminUser):
    return _work_order_response(app.send_quote(work_order_id))


@router.post(
    "/work-orders/{work_order_id}/finish", response_model=WorkOrderRead, tags=["Ordens de servico"]
)
def finish_work_order(work_order_id: str, app: Application, _admin: AdminUser):
    return _work_order_response(app.finish_work_order(work_order_id))


@router.post(
    "/work-orders/{work_order_id}/deliver", response_model=WorkOrderRead, tags=["Ordens de servico"]
)
def deliver_work_order(work_order_id: str, app: Application, _admin: AdminUser):
    return _work_order_response(app.deliver_work_order(work_order_id))


@router.get(
    "/metrics/average-execution-time",
    response_model=AverageExecutionTime,
    tags=["Metricas"],
)
def average_execution_time(app: Application, _admin: AdminUser):
    return app.average_execution_time()


# Customer-facing API: tracking code + document prevent simple enumeration.
@router.get(
    "/public/work-orders/{tracking_code}",
    response_model=PublicWorkOrderRead,
    tags=["Cliente"],
)
def public_work_order(tracking_code: str, document: str, app: Application):
    return _work_order_response(app.get_public_work_order(tracking_code, document))


@router.post(
    "/public/work-orders/{tracking_code}/quote-decision",
    response_model=PublicWorkOrderRead,
    tags=["Cliente"],
)
def quote_decision(tracking_code: str, payload: QuoteDecision, app: Application):
    return _work_order_response(app.decide_quote(tracking_code, payload.document, payload.approved))
