from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from garage.domain.enums import QuoteStatus, WorkOrderStatus


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class TokenRequest(ApiModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(ApiModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - tipo do token, nao e credencial
    expires_in: int


class CustomerBase(ApiModel):
    name: str = Field(min_length=2, max_length=160)
    document: str = Field(min_length=11, max_length=18)
    email: EmailStr
    phone: str = Field(min_length=8, max_length=30)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    document: str | None = Field(default=None, min_length=11, max_length=18)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=8, max_length=30)


class CustomerRead(CustomerBase):
    id: str
    created_at: datetime
    updated_at: datetime


class VehicleBase(ApiModel):
    customer_id: str
    plate: str = Field(min_length=7, max_length=8)
    brand: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1900, le=date.today().year + 1)


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(ApiModel):
    customer_id: str | None = None
    plate: str | None = Field(default=None, min_length=7, max_length=8)
    brand: str | None = Field(default=None, min_length=1, max_length=80)
    model: str | None = Field(default=None, min_length=1, max_length=100)
    year: int | None = Field(default=None, ge=1900, le=date.today().year + 1)


class VehicleRead(VehicleBase):
    id: str
    created_at: datetime
    updated_at: datetime


class CatalogServiceBase(ApiModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    price: Decimal = Field(ge=0, decimal_places=2, max_digits=12)
    estimated_minutes: int = Field(gt=0, le=100_000)
    active: bool = True


class CatalogServiceCreate(CatalogServiceBase):
    pass


class CatalogServiceUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    estimated_minutes: int | None = Field(default=None, gt=0, le=100_000)
    active: bool | None = None


class CatalogServiceRead(CatalogServiceBase):
    id: str
    created_at: datetime
    updated_at: datetime


class PartBase(ApiModel):
    name: str = Field(min_length=2, max_length=120)
    sku: str = Field(min_length=1, max_length=60)
    unit_price: Decimal = Field(ge=0, decimal_places=2, max_digits=12)
    active: bool = True


class PartCreate(PartBase):
    stock_quantity: int = Field(default=0, ge=0)


class PartUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    sku: str | None = Field(default=None, min_length=1, max_length=60)
    unit_price: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    active: bool | None = None


class PartRead(PartBase):
    id: str
    stock_quantity: int
    created_at: datetime
    updated_at: datetime


class StockAdjustment(ApiModel):
    quantity_delta: int = Field(ge=-1_000_000, le=1_000_000)
    reason: str = Field(min_length=3, max_length=200)

    @field_validator("quantity_delta")
    @classmethod
    def quantity_cannot_be_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("O ajuste nao pode ser zero.")
        return value


class VehicleForOrder(ApiModel):
    plate: str = Field(min_length=7, max_length=8)
    brand: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1900, le=date.today().year + 1)


class ItemReference(ApiModel):
    id: str
    quantity: int = Field(default=1, gt=0, le=10_000)


class WorkOrderCreate(ApiModel):
    customer_document: str = Field(min_length=11, max_length=18)
    vehicle: VehicleForOrder
    services: list[ItemReference] = Field(min_length=1)
    parts: list[ItemReference] = Field(default_factory=list)
    notes: str = Field(default="", max_length=5000)


class WorkOrderItemsReplace(ApiModel):
    services: list[ItemReference] = Field(min_length=1)
    parts: list[ItemReference] = Field(default_factory=list)


class QuoteDecision(ApiModel):
    document: str = Field(min_length=11, max_length=18)
    approved: bool


class WorkOrderItemRead(ApiModel):
    reference_id: str
    description: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal


class WorkOrderRead(ApiModel):
    id: str
    tracking_code: str
    customer_id: str
    vehicle_id: str
    vehicle_plate: str
    notes: str
    status: WorkOrderStatus
    quote_status: QuoteStatus
    quote_total: Decimal
    services: list[WorkOrderItemRead]
    parts: list[WorkOrderItemRead]
    created_at: datetime
    updated_at: datetime
    diagnosis_started_at: datetime | None
    approved_at: datetime | None
    execution_started_at: datetime | None
    finalized_at: datetime | None
    delivered_at: datetime | None


class PublicWorkOrderRead(ApiModel):
    tracking_code: str
    vehicle_plate: str
    status: WorkOrderStatus
    quote_status: QuoteStatus
    quote_total: Decimal
    services: list[WorkOrderItemRead]
    parts: list[WorkOrderItemRead]
    updated_at: datetime


class AverageExecutionTime(ApiModel):
    completed_orders: int
    average_minutes: float | None


class HealthResponse(ApiModel):
    status: str
