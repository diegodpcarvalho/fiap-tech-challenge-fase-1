from datetime import UTC, datetime
from decimal import Decimal

import pytest

from garage.domain.entities import WorkOrderAggregate, WorkOrderItem
from garage.domain.enums import QuoteStatus, WorkOrderStatus
from garage.domain.exceptions import InvalidTransitionError, ValidationError


def item(reference: str = "service-1", price: str = "100.00", quantity: int = 1):
    return WorkOrderItem(reference, "Troca de oleo", Decimal(price), quantity)


def order() -> WorkOrderAggregate:
    return WorkOrderAggregate(
        id="order-1",
        tracking_code="OS-ABC",
        customer_id="customer-1",
        vehicle_id="vehicle-1",
        service_items=[item()],
        part_items=[item("part-1", "25.50", 2)],
    )


def test_complete_work_order_lifecycle():
    work_order = order()
    assert work_order.quote_total == Decimal("151.00")
    assert work_order.status == WorkOrderStatus.RECEIVED

    at = datetime(2026, 1, 1, tzinfo=UTC)
    work_order.start_diagnosis(at)
    assert work_order.diagnosis_started_at == at
    work_order.send_quote()
    assert work_order.quote_status == QuoteStatus.PENDING
    work_order.decide_quote(True, at)
    assert work_order.status == WorkOrderStatus.IN_PROGRESS
    assert work_order.approved_at == at
    work_order.finish(at)
    assert work_order.finalized_at == at
    work_order.deliver(at)
    assert work_order.status == WorkOrderStatus.DELIVERED


def test_rejected_quote_can_be_revised():
    work_order = order()
    work_order.start_diagnosis()
    work_order.send_quote()
    work_order.decide_quote(False)
    assert work_order.quote_status == QuoteStatus.REJECTED
    work_order.replace_items([item(price="120")], [])
    assert work_order.status == WorkOrderStatus.IN_DIAGNOSIS
    assert work_order.quote_status == QuoteStatus.DRAFT
    assert work_order.quote_total == Decimal("120.00")


def test_rejected_quote_can_be_delivered_without_execution():
    work_order = order()
    at = datetime(2026, 1, 1, tzinfo=UTC)
    work_order.start_diagnosis()
    work_order.send_quote()
    work_order.decide_quote(False)
    work_order.deliver(at)
    assert work_order.status == WorkOrderStatus.DELIVERED
    assert work_order.quote_status == QuoteStatus.REJECTED
    assert work_order.execution_started_at is None
    assert work_order.finalized_at is None
    assert work_order.delivered_at == at


def test_items_cannot_change_during_execution():
    work_order = order()
    work_order.start_diagnosis()
    work_order.send_quote()
    work_order.decide_quote(True)
    with pytest.raises(InvalidTransitionError, match="itens"):
        work_order.replace_items([item(price="200")], [])


def test_invalid_transition_is_rejected():
    with pytest.raises(InvalidTransitionError, match="esperado"):
        order().finish()


def test_order_requires_a_service():
    with pytest.raises(ValidationError, match="ao menos um servico"):
        WorkOrderAggregate(
            id="1", tracking_code="OS-1", customer_id="1", vehicle_id="1", service_items=[]
        )


def test_order_rejects_repeated_or_invalid_items():
    with pytest.raises(ValidationError, match="repita"):
        WorkOrderAggregate(
            id="1",
            tracking_code="OS-1",
            customer_id="1",
            vehicle_id="1",
            service_items=[item(), item()],
        )
    with pytest.raises(ValidationError, match="quantidade"):
        WorkOrderAggregate(
            id="1",
            tracking_code="OS-1",
            customer_id="1",
            vehicle_id="1",
            service_items=[item(quantity=0)],
        )


def test_quote_can_only_be_decided_once():
    work_order = order()
    work_order.start_diagnosis()
    work_order.send_quote()
    work_order.decide_quote(False)
    with pytest.raises(InvalidTransitionError, match="pendente"):
        work_order.decide_quote(True)
