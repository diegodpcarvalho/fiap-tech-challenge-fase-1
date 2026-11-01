from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from garage.domain.enums import QuoteStatus, WorkOrderStatus
from garage.domain.exceptions import InvalidTransitionError, ValidationError
from garage.domain.value_objects import Money


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class WorkOrderItem:
    reference_id: str
    description: str
    unit_price: Decimal
    quantity: int

    def subtotal(self) -> Money:
        return Money(self.unit_price).multiply(self.quantity)


@dataclass(slots=True)
class WorkOrderAggregate:
    id: str
    tracking_code: str
    customer_id: str
    vehicle_id: str
    notes: str = ""
    status: WorkOrderStatus = WorkOrderStatus.RECEIVED
    quote_status: QuoteStatus = QuoteStatus.DRAFT
    service_items: list[WorkOrderItem] = field(default_factory=list)
    part_items: list[WorkOrderItem] = field(default_factory=list)
    quote_total: Decimal = Decimal("0.00")
    created_at: datetime = field(default_factory=utc_now)
    diagnosis_started_at: datetime | None = None
    approved_at: datetime | None = None
    execution_started_at: datetime | None = None
    finalized_at: datetime | None = None
    delivered_at: datetime | None = None

    def __post_init__(self) -> None:
        self.replace_items(self.service_items, self.part_items, initializing=True)

    def replace_items(
        self,
        services: list[WorkOrderItem],
        parts: list[WorkOrderItem],
        *,
        initializing: bool = False,
    ) -> None:
        editable = {WorkOrderStatus.RECEIVED, WorkOrderStatus.IN_DIAGNOSIS}
        if not initializing and self.status not in editable:
            if not (
                self.status == WorkOrderStatus.WAITING_APPROVAL
                and self.quote_status == QuoteStatus.REJECTED
            ):
                raise InvalidTransitionError("Os itens nao podem ser alterados nesta etapa.")
            self.status = WorkOrderStatus.IN_DIAGNOSIS
            self.quote_status = QuoteStatus.DRAFT
        if not services:
            raise ValidationError("A ordem de servico deve possuir ao menos um servico.")
        references = [item.reference_id for item in services]
        part_references = [item.reference_id for item in parts]
        if len(references) != len(set(references)) or len(part_references) != len(
            set(part_references)
        ):
            raise ValidationError("Nao repita o mesmo servico ou peca na ordem.")
        if any(item.quantity <= 0 for item in [*services, *parts]):
            raise ValidationError("A quantidade dos itens deve ser maior que zero.")
        self.service_items = list(services)
        self.part_items = list(parts)
        total = Money(0)
        for item in [*services, *parts]:
            total = total + item.subtotal()
        self.quote_total = total.value

    def start_diagnosis(self, at: datetime | None = None) -> None:
        self._require_status(WorkOrderStatus.RECEIVED)
        self.status = WorkOrderStatus.IN_DIAGNOSIS
        self.diagnosis_started_at = at or utc_now()

    def send_quote(self) -> None:
        self._require_status(WorkOrderStatus.IN_DIAGNOSIS)
        self.status = WorkOrderStatus.WAITING_APPROVAL
        self.quote_status = QuoteStatus.PENDING

    def decide_quote(self, approved: bool, at: datetime | None = None) -> None:
        self._require_status(WorkOrderStatus.WAITING_APPROVAL)
        if self.quote_status != QuoteStatus.PENDING:
            raise InvalidTransitionError("O orcamento nao esta pendente de decisao.")
        if approved:
            current_time = at or utc_now()
            self.quote_status = QuoteStatus.APPROVED
            self.status = WorkOrderStatus.IN_PROGRESS
            self.approved_at = current_time
            self.execution_started_at = current_time
        else:
            self.quote_status = QuoteStatus.REJECTED

    def finish(self, at: datetime | None = None) -> None:
        self._require_status(WorkOrderStatus.IN_PROGRESS)
        self.status = WorkOrderStatus.COMPLETED
        self.finalized_at = at or utc_now()

    def deliver(self, at: datetime | None = None) -> None:
        completed_service = self.status == WorkOrderStatus.COMPLETED
        rejected_without_service = (
            self.status == WorkOrderStatus.WAITING_APPROVAL
            and self.quote_status == QuoteStatus.REJECTED
        )
        if not (completed_service or rejected_without_service):
            raise InvalidTransitionError(
                "A entrega exige servico finalizado ou orcamento rejeitado."
            )
        self.status = WorkOrderStatus.DELIVERED
        self.delivered_at = at or utc_now()

    def _require_status(self, expected: WorkOrderStatus) -> None:
        if self.status != expected:
            raise InvalidTransitionError(
                f"Transicao invalida: esperado {expected.value}, atual {self.status.value}."
            )
