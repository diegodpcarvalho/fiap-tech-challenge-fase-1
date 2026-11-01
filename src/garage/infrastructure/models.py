from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from garage.domain.entities import utc_now
from garage.domain.enums import QuoteStatus, WorkOrderStatus
from garage.infrastructure.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class AdminUserModel(Base, TimestampMixin):
    __tablename__ = "admin_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class CustomerModel(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(160))
    document: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254))
    phone: Mapped[str] = mapped_column(String(30))

    vehicles: Mapped[list[VehicleModel]] = relationship(back_populates="customer")
    work_orders: Mapped[list[WorkOrderModel]] = relationship(back_populates="customer")


class VehicleModel(Base, TimestampMixin):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"))
    plate: Mapped[str] = mapped_column(String(7), unique=True, index=True)
    brand: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer)

    customer: Mapped[CustomerModel] = relationship(back_populates="vehicles")
    work_orders: Mapped[list[WorkOrderModel]] = relationship(back_populates="vehicle")


class CatalogServiceModel(Base, TimestampMixin):
    __tablename__ = "catalog_services"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_service_price_nonnegative"),
        CheckConstraint("estimated_minutes > 0", name="ck_service_minutes_positive"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PartModel(Base, TimestampMixin):
    __tablename__ = "parts"
    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="ck_part_price_nonnegative"),
        CheckConstraint("stock_quantity >= 0", name="ck_part_stock_nonnegative"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120))
    sku: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkOrderModel(Base, TimestampMixin):
    __tablename__ = "work_orders"
    __table_args__ = (Index("ix_work_orders_status_created", "status", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tracking_code: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"))
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id", ondelete="RESTRICT"))
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default=WorkOrderStatus.RECEIVED.value)
    quote_status: Mapped[str] = mapped_column(String(20), default=QuoteStatus.DRAFT.value)
    quote_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    diagnosis_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    execution_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer: Mapped[CustomerModel] = relationship(back_populates="work_orders")
    vehicle: Mapped[VehicleModel] = relationship(back_populates="work_orders")
    service_items: Mapped[list[WorkOrderServiceItemModel]] = relationship(
        cascade="all, delete-orphan", back_populates="work_order", lazy="selectin"
    )
    part_items: Mapped[list[WorkOrderPartItemModel]] = relationship(
        cascade="all, delete-orphan", back_populates="work_order", lazy="selectin"
    )


class WorkOrderServiceItemModel(Base):
    __tablename__ = "work_order_service_items"
    __table_args__ = (
        UniqueConstraint("work_order_id", "service_id", name="uq_order_service"),
        CheckConstraint("quantity > 0", name="ck_order_service_quantity_positive"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    work_order_id: Mapped[str] = mapped_column(ForeignKey("work_orders.id", ondelete="CASCADE"))
    service_id: Mapped[str] = mapped_column(ForeignKey("catalog_services.id", ondelete="RESTRICT"))
    description_snapshot: Mapped[str] = mapped_column(String(120))
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quantity: Mapped[int] = mapped_column(Integer)

    work_order: Mapped[WorkOrderModel] = relationship(back_populates="service_items")


class WorkOrderPartItemModel(Base):
    __tablename__ = "work_order_part_items"
    __table_args__ = (
        UniqueConstraint("work_order_id", "part_id", name="uq_order_part"),
        CheckConstraint("quantity > 0", name="ck_order_part_quantity_positive"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    work_order_id: Mapped[str] = mapped_column(ForeignKey("work_orders.id", ondelete="CASCADE"))
    part_id: Mapped[str] = mapped_column(ForeignKey("parts.id", ondelete="RESTRICT"))
    description_snapshot: Mapped[str] = mapped_column(String(120))
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quantity: Mapped[int] = mapped_column(Integer)

    work_order: Mapped[WorkOrderModel] = relationship(back_populates="part_items")


class StockMovementModel(Base):
    __tablename__ = "stock_movements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    part_id: Mapped[str] = mapped_column(ForeignKey("parts.id", ondelete="RESTRICT"), index=True)
    work_order_id: Mapped[str | None] = mapped_column(
        ForeignKey("work_orders.id", ondelete="RESTRICT"), index=True
    )
    movement_type: Mapped[str] = mapped_column(String(10))
    quantity: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
