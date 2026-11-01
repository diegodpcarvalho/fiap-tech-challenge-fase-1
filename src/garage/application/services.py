from __future__ import annotations

import secrets
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from garage.domain.entities import WorkOrderAggregate, WorkOrderItem
from garage.domain.enums import QuoteStatus, StockMovementType, WorkOrderStatus
from garage.domain.exceptions import ConflictError, InsufficientStockError, NotFoundError
from garage.domain.value_objects import Document, LicensePlate, Money
from garage.infrastructure.models import (
    AdminUserModel,
    CatalogServiceModel,
    CustomerModel,
    PartModel,
    StockMovementModel,
    VehicleModel,
    WorkOrderModel,
    WorkOrderPartItemModel,
    WorkOrderServiceItemModel,
)


class GarageApplication:
    """Fachada transacional dos casos de uso do monolito."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def authenticate(self, username: str) -> AdminUserModel | None:
        return self.session.scalar(
            select(AdminUserModel).where(
                AdminUserModel.username == username, AdminUserModel.active.is_(True)
            )
        )

    # Customers
    def create_customer(self, data: dict[str, Any]) -> CustomerModel:
        document = Document(data["document"]).value
        self._ensure_unique(CustomerModel, CustomerModel.document, document, "CPF/CNPJ")
        data["document"] = document
        customer = CustomerModel(**data)
        return self._save(customer)

    def list_customers(self, offset: int = 0, limit: int = 100) -> list[CustomerModel]:
        return list(
            self.session.scalars(
                select(CustomerModel).order_by(CustomerModel.name).offset(offset).limit(limit)
            )
        )

    def get_customer(self, customer_id: str) -> CustomerModel:
        return self._get_or_raise(CustomerModel, customer_id, "Cliente")

    def update_customer(self, customer_id: str, data: dict[str, Any]) -> CustomerModel:
        customer = self.get_customer(customer_id)
        if "document" in data:
            document = Document(data["document"]).value
            self._ensure_unique(
                CustomerModel, CustomerModel.document, document, "CPF/CNPJ", excluding=customer_id
            )
            data["document"] = document
        self._assign(customer, data)
        return self._save(customer)

    def delete_customer(self, customer_id: str) -> None:
        customer = self.get_customer(customer_id)
        order_count = self.session.scalar(
            select(func.count())
            .select_from(WorkOrderModel)
            .where(WorkOrderModel.customer_id == customer_id)
        )
        if order_count:
            raise ConflictError("Cliente possui ordens de servico e nao pode ser removido.")
        self.session.delete(customer)
        self.session.commit()

    # Vehicles
    def create_vehicle(self, data: dict[str, Any]) -> VehicleModel:
        self.get_customer(data["customer_id"])
        plate = LicensePlate(data["plate"]).value
        self._ensure_unique(VehicleModel, VehicleModel.plate, plate, "Placa")
        data["plate"] = plate
        vehicle = VehicleModel(**data)
        return self._save(vehicle)

    def list_vehicles(
        self, customer_id: str | None = None, offset: int = 0, limit: int = 100
    ) -> list[VehicleModel]:
        statement = select(VehicleModel).order_by(VehicleModel.plate)
        if customer_id:
            statement = statement.where(VehicleModel.customer_id == customer_id)
        return list(self.session.scalars(statement.offset(offset).limit(limit)))

    def get_vehicle(self, vehicle_id: str) -> VehicleModel:
        return self._get_or_raise(VehicleModel, vehicle_id, "Veiculo")

    def update_vehicle(self, vehicle_id: str, data: dict[str, Any]) -> VehicleModel:
        vehicle = self.get_vehicle(vehicle_id)
        if "customer_id" in data:
            self.get_customer(data["customer_id"])
        if "plate" in data:
            plate = LicensePlate(data["plate"]).value
            self._ensure_unique(
                VehicleModel, VehicleModel.plate, plate, "Placa", excluding=vehicle_id
            )
            data["plate"] = plate
        self._assign(vehicle, data)
        return self._save(vehicle)

    def delete_vehicle(self, vehicle_id: str) -> None:
        vehicle = self.get_vehicle(vehicle_id)
        order_count = self.session.scalar(
            select(func.count())
            .select_from(WorkOrderModel)
            .where(WorkOrderModel.vehicle_id == vehicle_id)
        )
        if order_count:
            raise ConflictError("Veiculo possui ordens de servico e nao pode ser removido.")
        self.session.delete(vehicle)
        self.session.commit()

    # Service catalog
    def create_catalog_service(self, data: dict[str, Any]) -> CatalogServiceModel:
        self._ensure_unique(
            CatalogServiceModel, CatalogServiceModel.name, data["name"], "Nome do servico"
        )
        data["price"] = Money(data["price"]).value
        model = CatalogServiceModel(**data)
        return self._save(model)

    def list_catalog_services(
        self, include_inactive: bool = False, offset: int = 0, limit: int = 100
    ) -> list[CatalogServiceModel]:
        statement = select(CatalogServiceModel).order_by(CatalogServiceModel.name)
        if not include_inactive:
            statement = statement.where(CatalogServiceModel.active.is_(True))
        return list(self.session.scalars(statement.offset(offset).limit(limit)))

    def get_catalog_service(self, service_id: str) -> CatalogServiceModel:
        return self._get_or_raise(CatalogServiceModel, service_id, "Servico")

    def update_catalog_service(self, service_id: str, data: dict[str, Any]) -> CatalogServiceModel:
        service = self.get_catalog_service(service_id)
        if "name" in data:
            self._ensure_unique(
                CatalogServiceModel,
                CatalogServiceModel.name,
                data["name"],
                "Nome do servico",
                excluding=service_id,
            )
        if "price" in data:
            data["price"] = Money(data["price"]).value
        self._assign(service, data)
        return self._save(service)

    def delete_catalog_service(self, service_id: str) -> None:
        service = self.get_catalog_service(service_id)
        service.active = False
        self._save(service)

    # Parts and stock
    def create_part(self, data: dict[str, Any]) -> PartModel:
        normalized_sku = data["sku"].strip().upper()
        self._ensure_unique(PartModel, PartModel.sku, normalized_sku, "SKU")
        data["sku"] = normalized_sku
        data["unit_price"] = Money(data["unit_price"]).value
        part = PartModel(**data)
        saved = self._save(part)
        if saved.stock_quantity:
            self._record_stock_movement(
                saved, saved.stock_quantity, StockMovementType.ENTRY, "Estoque inicial"
            )
            self.session.commit()
        return saved

    def list_parts(
        self, include_inactive: bool = False, offset: int = 0, limit: int = 100
    ) -> list[PartModel]:
        statement = select(PartModel).order_by(PartModel.name)
        if not include_inactive:
            statement = statement.where(PartModel.active.is_(True))
        return list(self.session.scalars(statement.offset(offset).limit(limit)))

    def get_part(self, part_id: str) -> PartModel:
        return self._get_or_raise(PartModel, part_id, "Peca ou insumo")

    def update_part(self, part_id: str, data: dict[str, Any]) -> PartModel:
        part = self.get_part(part_id)
        data.pop("stock_quantity", None)
        if "sku" in data:
            normalized_sku = data["sku"].strip().upper()
            self._ensure_unique(PartModel, PartModel.sku, normalized_sku, "SKU", excluding=part_id)
            data["sku"] = normalized_sku
        if "unit_price" in data:
            data["unit_price"] = Money(data["unit_price"]).value
        self._assign(part, data)
        return self._save(part)

    def adjust_stock(self, part_id: str, quantity_delta: int, reason: str) -> PartModel:
        part = self.session.scalar(
            select(PartModel).where(PartModel.id == part_id).with_for_update()
        )
        if not part:
            raise NotFoundError("Peca ou insumo nao encontrado.")
        resulting_stock = part.stock_quantity + quantity_delta
        if resulting_stock < 0:
            raise InsufficientStockError("Ajuste deixaria o estoque negativo.")
        part.stock_quantity = resulting_stock
        movement_type = StockMovementType.ENTRY if quantity_delta > 0 else StockMovementType.EXIT
        self._record_stock_movement(part, abs(quantity_delta), movement_type, reason)
        self.session.commit()
        self.session.refresh(part)
        return part

    def delete_part(self, part_id: str) -> None:
        part = self.get_part(part_id)
        part.active = False
        self._save(part)

    # Work orders
    def create_work_order(self, data: dict[str, Any]) -> WorkOrderModel:
        document = Document(data["customer_document"]).value
        customer = self.session.scalar(
            select(CustomerModel).where(CustomerModel.document == document)
        )
        if not customer:
            raise NotFoundError("Cliente nao encontrado para o CPF/CNPJ informado.")

        vehicle_data = data["vehicle"]
        plate = LicensePlate(vehicle_data["plate"]).value
        vehicle = self.session.scalar(select(VehicleModel).where(VehicleModel.plate == plate))
        if vehicle and vehicle.customer_id != customer.id:
            raise ConflictError("A placa informada pertence a outro cliente.")
        if not vehicle:
            vehicle = VehicleModel(
                customer_id=customer.id,
                plate=plate,
                **{key: value for key, value in vehicle_data.items() if key != "plate"},
            )
            self.session.add(vehicle)
            self.session.flush()

        services, parts = self._load_order_items(data["services"], data.get("parts", []))
        tracking_code = self._new_tracking_code()
        aggregate = WorkOrderAggregate(
            id="pending",
            tracking_code=tracking_code,
            customer_id=customer.id,
            vehicle_id=vehicle.id,
            notes=data.get("notes", ""),
            service_items=services,
            part_items=parts,
        )
        work_order = WorkOrderModel(
            tracking_code=tracking_code,
            customer_id=customer.id,
            vehicle_id=vehicle.id,
            notes=aggregate.notes,
            status=aggregate.status.value,
            quote_status=aggregate.quote_status.value,
            quote_total=aggregate.quote_total,
        )
        self._set_model_items(work_order, services, parts)
        self.session.add(work_order)
        self.session.commit()
        return self.get_work_order(work_order.id)

    def list_work_orders(
        self,
        status: WorkOrderStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[WorkOrderModel]:
        statement = self._work_order_statement().order_by(WorkOrderModel.created_at.desc())
        if status:
            statement = statement.where(WorkOrderModel.status == status.value)
        return list(self.session.scalars(statement.offset(offset).limit(limit)).unique())

    def get_work_order(self, work_order_id: str) -> WorkOrderModel:
        model = self.session.scalar(
            self._work_order_statement().where(WorkOrderModel.id == work_order_id)
        )
        if not model:
            raise NotFoundError("Ordem de servico nao encontrada.")
        return model

    def get_public_work_order(self, tracking_code: str, document: str) -> WorkOrderModel:
        normalized_document = Document(document).value
        model = self.session.scalar(
            self._work_order_statement()
            .join(CustomerModel, CustomerModel.id == WorkOrderModel.customer_id)
            .where(
                WorkOrderModel.tracking_code == tracking_code.upper(),
                CustomerModel.document == normalized_document,
            )
        )
        if not model:
            raise NotFoundError("Ordem de servico nao encontrada.")
        return model

    def replace_work_order_items(
        self,
        work_order_id: str,
        services_data: list[dict[str, Any]],
        parts_data: list[dict[str, Any]],
    ) -> WorkOrderModel:
        model = self.get_work_order(work_order_id)
        aggregate = self._to_aggregate(model)
        services, parts = self._load_order_items(services_data, parts_data)
        aggregate.replace_items(services, parts)
        model.service_items.clear()
        model.part_items.clear()
        self.session.flush()
        self._set_model_items(model, services, parts)
        self._sync_aggregate(model, aggregate)
        self.session.commit()
        return self.get_work_order(work_order_id)

    def start_diagnosis(self, work_order_id: str) -> WorkOrderModel:
        return self._apply_transition(work_order_id, "start_diagnosis")

    def send_quote(self, work_order_id: str) -> WorkOrderModel:
        return self._apply_transition(work_order_id, "send_quote")

    def decide_quote(self, tracking_code: str, document: str, approved: bool) -> WorkOrderModel:
        model = self.get_public_work_order(tracking_code, document)
        aggregate = self._to_aggregate(model)
        if approved:
            part_ids = sorted(item.part_id for item in model.part_items)
            locked_parts = list(
                self.session.scalars(
                    select(PartModel).where(PartModel.id.in_(part_ids)).with_for_update()
                )
            )
            parts_by_id = {part.id: part for part in locked_parts}
            for item in model.part_items:
                part = parts_by_id.get(item.part_id)
                if not part or not part.active or part.stock_quantity < item.quantity:
                    description = item.description_snapshot
                    raise InsufficientStockError(f"Estoque insuficiente para: {description}.")
            aggregate.decide_quote(True)
            for item in model.part_items:
                part = parts_by_id[item.part_id]
                part.stock_quantity -= item.quantity
                self._record_stock_movement(
                    part,
                    item.quantity,
                    StockMovementType.EXIT,
                    f"Baixa pela OS {model.tracking_code}",
                    work_order_id=model.id,
                )
        else:
            aggregate.decide_quote(False)
        self._sync_aggregate(model, aggregate)
        self.session.commit()
        return self.get_work_order(model.id)

    def finish_work_order(self, work_order_id: str) -> WorkOrderModel:
        return self._apply_transition(work_order_id, "finish")

    def deliver_work_order(self, work_order_id: str) -> WorkOrderModel:
        return self._apply_transition(work_order_id, "deliver")

    def average_execution_time(self) -> dict[str, int | float | None]:
        rows = list(
            self.session.execute(
                select(WorkOrderModel.execution_started_at, WorkOrderModel.finalized_at).where(
                    WorkOrderModel.finalized_at.is_not(None),
                    WorkOrderModel.execution_started_at.is_not(None),
                )
            )
        )
        if not rows:
            return {"completed_orders": 0, "average_minutes": None}
        durations = [
            (finalized_at - started_at).total_seconds() / 60 for started_at, finalized_at in rows
        ]
        return {
            "completed_orders": len(durations),
            "average_minutes": round(sum(durations) / len(durations), 2),
        }

    def _apply_transition(self, work_order_id: str, method: str) -> WorkOrderModel:
        model = self.get_work_order(work_order_id)
        aggregate = self._to_aggregate(model)
        getattr(aggregate, method)()
        self._sync_aggregate(model, aggregate)
        self.session.commit()
        return self.get_work_order(work_order_id)

    def _load_order_items(
        self, services_data: list[dict[str, Any]], parts_data: list[dict[str, Any]]
    ) -> tuple[list[WorkOrderItem], list[WorkOrderItem]]:
        service_ids = [item["id"] for item in services_data]
        part_ids = [item["id"] for item in parts_data]
        services_by_id = {
            service.id: service
            for service in self.session.scalars(
                select(CatalogServiceModel).where(
                    CatalogServiceModel.id.in_(service_ids), CatalogServiceModel.active.is_(True)
                )
            )
        }
        parts_by_id = {
            part.id: part
            for part in self.session.scalars(
                select(PartModel).where(PartModel.id.in_(part_ids), PartModel.active.is_(True))
            )
        }
        if len(services_by_id) != len(set(service_ids)):
            raise NotFoundError("Um ou mais servicos nao existem ou estao inativos.")
        if len(parts_by_id) != len(set(part_ids)):
            raise NotFoundError("Uma ou mais pecas nao existem ou estao inativas.")
        services = [
            WorkOrderItem(
                reference_id=item["id"],
                description=services_by_id[item["id"]].name,
                unit_price=services_by_id[item["id"]].price,
                quantity=item["quantity"],
            )
            for item in services_data
        ]
        parts = [
            WorkOrderItem(
                reference_id=item["id"],
                description=parts_by_id[item["id"]].name,
                unit_price=parts_by_id[item["id"]].unit_price,
                quantity=item["quantity"],
            )
            for item in parts_data
        ]
        return services, parts

    @staticmethod
    def _set_model_items(
        model: WorkOrderModel, services: list[WorkOrderItem], parts: list[WorkOrderItem]
    ) -> None:
        model.service_items.extend(
            WorkOrderServiceItemModel(
                service_id=item.reference_id,
                description_snapshot=item.description,
                unit_price_snapshot=item.unit_price,
                quantity=item.quantity,
            )
            for item in services
        )
        model.part_items.extend(
            WorkOrderPartItemModel(
                part_id=item.reference_id,
                description_snapshot=item.description,
                unit_price_snapshot=item.unit_price,
                quantity=item.quantity,
            )
            for item in parts
        )

    @staticmethod
    def _to_aggregate(model: WorkOrderModel) -> WorkOrderAggregate:
        return WorkOrderAggregate(
            id=model.id,
            tracking_code=model.tracking_code,
            customer_id=model.customer_id,
            vehicle_id=model.vehicle_id,
            notes=model.notes,
            status=WorkOrderStatus(model.status),
            quote_status=QuoteStatus(model.quote_status),
            service_items=[
                WorkOrderItem(
                    reference_id=item.service_id,
                    description=item.description_snapshot,
                    unit_price=item.unit_price_snapshot,
                    quantity=item.quantity,
                )
                for item in model.service_items
            ],
            part_items=[
                WorkOrderItem(
                    reference_id=item.part_id,
                    description=item.description_snapshot,
                    unit_price=item.unit_price_snapshot,
                    quantity=item.quantity,
                )
                for item in model.part_items
            ],
            quote_total=model.quote_total,
            created_at=model.created_at,
            diagnosis_started_at=model.diagnosis_started_at,
            approved_at=model.approved_at,
            execution_started_at=model.execution_started_at,
            finalized_at=model.finalized_at,
            delivered_at=model.delivered_at,
        )

    @staticmethod
    def _sync_aggregate(model: WorkOrderModel, aggregate: WorkOrderAggregate) -> None:
        model.status = aggregate.status.value
        model.quote_status = aggregate.quote_status.value
        model.quote_total = aggregate.quote_total
        model.diagnosis_started_at = aggregate.diagnosis_started_at
        model.approved_at = aggregate.approved_at
        model.execution_started_at = aggregate.execution_started_at
        model.finalized_at = aggregate.finalized_at
        model.delivered_at = aggregate.delivered_at

    @staticmethod
    def _work_order_statement():
        return select(WorkOrderModel).options(
            selectinload(WorkOrderModel.service_items),
            selectinload(WorkOrderModel.part_items),
            selectinload(WorkOrderModel.vehicle),
        )

    def _record_stock_movement(
        self,
        part: PartModel,
        quantity: int,
        movement_type: StockMovementType,
        reason: str,
        work_order_id: str | None = None,
    ) -> None:
        self.session.add(
            StockMovementModel(
                part_id=part.id,
                work_order_id=work_order_id,
                movement_type=movement_type.value,
                quantity=quantity,
                reason=reason,
            )
        )

    def _new_tracking_code(self) -> str:
        for _attempt in range(5):
            code = f"OS-{secrets.token_hex(5).upper()}"
            exists = self.session.scalar(
                select(WorkOrderModel.id).where(WorkOrderModel.tracking_code == code)
            )
            if not exists:
                return code
        raise ConflictError("Nao foi possivel gerar o codigo de acompanhamento.")

    def _get_or_raise(self, model_type: type, object_id: str, label: str):
        model = self.session.get(model_type, object_id)
        if not model:
            raise NotFoundError(f"{label} nao encontrado.")
        return model

    def _ensure_unique(
        self, model_type: type, column, value: Any, label: str, excluding: str | None = None
    ) -> None:
        statement = select(model_type).where(column == value)
        if excluding:
            statement = statement.where(model_type.id != excluding)
        if self.session.scalar(statement):
            raise ConflictError(f"{label} ja cadastrado.")

    @staticmethod
    def _assign(model: Any, data: dict[str, Any]) -> None:
        for key, value in data.items():
            setattr(model, key, value)

    def _save(self, model):
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return model
