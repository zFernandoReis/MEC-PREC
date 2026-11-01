"""Migração aditiva e repetível do workflow; não inventa histórico de OS legadas."""
import asyncio

from sqlalchemy import text

from app.modules.orders.infrastructure.models.order_event_model import OrderEventModel
from app.modules.orders.infrastructure.models.orders_model import OrderModel  # registers FK metadata
from app.shared.infrastructure.database.engine import engine


async def migrate_connection(connection):
    for definition in (
        "version INTEGER NOT NULL DEFAULT 1",
        "budget_snapshot JSON",
        "approved_at TIMESTAMP WITH TIME ZONE",
        "approved_by INTEGER REFERENCES users(id)",
        "execution_started_at TIMESTAMP WITH TIME ZONE",
        "finished_at TIMESTAMP WITH TIME ZONE",
        "delivered_at TIMESTAMP WITH TIME ZONE",
    ):
        await connection.execute(text(f"ALTER TABLE orders ADD COLUMN IF NOT EXISTS {definition}"))
    await connection.execute(text(
        "ALTER TABLE budgets ADD COLUMN IF NOT EXISTS workflow_locked BOOLEAN NOT NULL DEFAULT false"
    ))
    # Legacy pending orders need a reference to approve, but no historical
    # consent, actor or timestamp is fabricated. Current terms require approval.
    await connection.execute(text("""
        UPDATE orders AS o SET budget_snapshot = json_build_object(
            'budget_id', b.budget_id, 'client_id', b.client_id, 'vehicle_id', b.vehicle_id,
            'technical_id', b.technical_id, 'service_name', b.service_name,
            'service_description', b.service_description, 'tools', b.tools, 'amount', b.amount,
            'duration_service_hours', b.duration_service_hours,
            'duration_service_days', b.duration_service_days
        ) FROM budgets AS b
        WHERE o.budget_id = b.budget_id AND o.order_status = 'aguardando_aprovacao'
          AND o.budget_snapshot IS NULL
    """))
    await connection.execute(text("""
        UPDATE budgets SET workflow_locked = true
        WHERE budget_id IN (
            SELECT budget_id FROM orders
            WHERE order_status IN ('aguardando_aprovacao', 'em_execucao', 'finalizada', 'entregue')
        ) AND workflow_locked = false
    """))
    await connection.run_sync(lambda sync: OrderEventModel.__table__.create(sync, checkfirst=True))


async def migrate():
    try:
        async with engine.begin() as connection:
            await migrate_connection(connection)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
