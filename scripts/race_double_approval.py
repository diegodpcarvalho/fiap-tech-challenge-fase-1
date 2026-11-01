from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from garage.application.services import GarageApplication
from garage.domain.enums import QuoteStatus, WorkOrderStatus
from garage.domain.exceptions import InvalidTransitionError
from garage.infrastructure.database import Base
from garage.infrastructure.models import (
    CatalogServiceModel,
    CustomerModel,
    PartModel,
    StockMovementModel,
    VehicleModel,
    WorkOrderModel,
    WorkOrderPartItemModel,
    WorkOrderServiceItemModel,
)


def _database_url_from_environment() -> str:
    explicit_url = os.getenv("POSTGRES_TEST_DATABASE_URL")
    if explicit_url:
        return explicit_url
    source_url = os.environ["DATABASE_URL"]
    database_name = os.getenv("TEST_DATABASE_NAME", "garage_test")
    return make_url(source_url).set(database=database_name).render_as_string(hide_password=False)


def run_concurrency_check(database_url: str, parallel: int = 20) -> dict[str, int]:
    url = make_url(database_url)
    if not url.database or not url.database.endswith("_test"):
        raise RuntimeError("O verificador aceita somente banco com nome terminado em '_test'.")

    engine = create_engine(url, pool_size=parallel, max_overflow=0, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        with sessions() as session:
            customer = CustomerModel(
                name="Maria",
                document="52998224725",
                email="maria@example.com",
                phone="11999999999",
            )
            vehicle = VehicleModel(
                customer=customer, plate="ABC1D23", brand="Honda", model="Civic", year=2022
            )
            service = CatalogServiceModel(
                name="Troca", description="", price=Decimal("100.00"), estimated_minutes=30
            )
            part = PartModel(
                name="Filtro",
                sku="F-CONCORRENCIA",
                unit_price=Decimal("25.00"),
                stock_quantity=10,
            )
            session.add_all([customer, vehicle, service, part])
            session.flush()
            order = WorkOrderModel(
                tracking_code="OS-CONCORRENCIA",
                customer=customer,
                vehicle=vehicle,
                status=WorkOrderStatus.WAITING_APPROVAL.value,
                quote_status=QuoteStatus.PENDING.value,
                quote_total=Decimal("150.00"),
            )
            order.service_items.append(
                WorkOrderServiceItemModel(
                    service_id=service.id,
                    description_snapshot=service.name,
                    unit_price_snapshot=service.price,
                    quantity=1,
                )
            )
            order.part_items.append(
                WorkOrderPartItemModel(
                    part_id=part.id,
                    description_snapshot=part.name,
                    unit_price_snapshot=part.unit_price,
                    quantity=2,
                )
            )
            session.add(order)
            session.commit()
            order_id = order.id
            part_id = part.id

        barrier = Barrier(parallel)

        def approve_once(_attempt: int) -> int:
            with sessions() as session:
                barrier.wait()
                try:
                    GarageApplication(session).decide_quote("OS-CONCORRENCIA", "52998224725", True)
                except InvalidTransitionError:
                    return 409
                return 200

        with ThreadPoolExecutor(max_workers=parallel) as executor:
            results = list(executor.map(approve_once, range(parallel)))

        with sessions() as session:
            stock = session.get(PartModel, part_id).stock_quantity
            movements = session.scalar(
                select(func.count())
                .select_from(StockMovementModel)
                .where(StockMovementModel.work_order_id == order_id)
            )
        return {
            "accepted": results.count(200),
            "conflicts": results.count(409),
            "stock": stock,
            "movements": movements,
        }
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


if __name__ == "__main__":
    outcome = run_concurrency_check(_database_url_from_environment())
    print(f"aprovacoes aceitas: {outcome['accepted']}")
    print(f"conflitos recusados: {outcome['conflicts']}")
    print(f"estoque final: {outcome['stock']}")
    print(f"movimentos de estoque: {outcome['movements']}")
    if outcome != {"accepted": 1, "conflicts": 19, "stock": 8, "movements": 1}:
        raise SystemExit("Falha: a aprovacao concorrente nao foi serializada.")
