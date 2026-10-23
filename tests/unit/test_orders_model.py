from datetime import date, datetime, timezone

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import CreateTable

from app.modules.orders.domain.entities.orders import Order
from app.modules.orders.domain.enums.order_status import OrderStatus
from app.modules.orders.infrastructure.models.orders_model import OrderModel


def test_order_foreign_keys_and_relationships():
    configure_mappers()
    targets = {
        "technical_id": ("users", "id", "technical"),
        "client_id": ("users", "id", "client"),
        "technical_responser_id": ("users", "id", "technical_responser"),
        "vehicle_id": ("vehicles", "vehicle_id", "vehicle"),
        "budget_id": ("budgets", "budget_id", "budget"),
    }
    ddl = str(CreateTable(OrderModel.__table__).compile(dialect=dialect()))
    for name, (table, key, relationship) in targets.items():
        column = OrderModel.__table__.c[name]
        assert not column.nullable
        assert next(iter(column.foreign_keys)).target_fullname == f"{table}.{key}"
        assert inspect(OrderModel).relationships[relationship].local_columns == {column}
        assert f"FOREIGN KEY({name}) REFERENCES {table} ({key})" in ddl


def test_order_entity_conversion_preserves_all_fields():
    order = Order(
        order_id=10,
        client_id=1,
        client_email="client@example.com",
        technical_id=2,
        technical_name="Técnico",
        technical_email="technical@example.com",
        technical_responser_id=3,
        technical_responser_name="Responsável",
        technical_responser_email="responsible@example.com",
        vehicle_id=4,
        budget_id=5,
        service_name="Revisão",
        duration_service_hours=2.5,
        order_status=OrderStatus.EM_EXECUCAO,
    )
    assert OrderModel.from_entity(order).to_entity() == order

    order.service_description = "Revisão completa"
    order.duration_service_days = 1
    order.service_date_start = date(2026, 10, 21)
    order.service_date_end = date(2026, 10, 22)
    order.create_at = datetime(2026, 10, 21, tzinfo=timezone.utc)
    order.update_at = datetime(2026, 10, 22, tzinfo=timezone.utc)
    assert OrderModel.from_entity(order).to_entity() == order
