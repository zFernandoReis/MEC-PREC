from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.modules.orders.domain.enums.order_status import OrderStatus
from app.modules.orders.domain.enums.notification_type import NotificationType
from app.modules.orders.infrastructure.jobs.notify_overdue_orders import NotifyOverdueOrdersJob
from app.modules.orders.infrastructure.jobs.notify_upcoming_orders import NotifyUpcomingOrdersJob
from app.modules.orders.infrastructure.models.notification_model import NotificationModel
from app.modules.orders.infrastructure.models.orders_model import OrderModel
from app.modules.users.domain.enums.user_role import UserRole
from app.modules.users.infrastructure.models.users_model import UserModel


@pytest.fixture
def job_session():
    engine = create_engine("sqlite://")
    for model in (UserModel, OrderModel, NotificationModel):
        model.__table__.create(engine)
    try:
        with Session(engine) as sync_session:
            sync_session.add(UserModel(
                id=1, primary_name="Cliente", secondary_name="Teste", cpf="52998224725",
                email="client@example.com", role=UserRole.CLIENT, cep="01001000",
                street="Praça", neighborhood="Sé", city="São Paulo", state="SP",
            ))
            sync_session.commit()
            session = AsyncMock(spec=AsyncSession)
            for method in ("add", "execute", "commit", "rollback"):
                getattr(session, method).side_effect = getattr(sync_session, method)
            yield sync_session, session
    finally:
        engine.dispose()


def add_order(session, end, status=OrderStatus.EM_EXECUCAO):
    order = OrderModel(
        client_id=1, client_email="client@example.com", technical_id=1,
        technical_name="Técnico", technical_email="tech@example.com",
        technical_responser_id=1, technical_responser_name="Responsável",
        technical_responser_email="responsible@example.com", vehicle_id=1, budget_id=1,
        service_name="Revisão", service_description="Revisão completa",
        duration_service_hours=2, duration_service_days=1, order_status=status,
        service_date_start=date(2026, 10, 20), service_date_end=end,
    )
    session.add(order)
    session.commit()
    return order


async def test_deadline_boundaries_batches_and_repeated_runs(job_session):
    sync_session, session = job_session
    today = date(2026, 10, 25)
    orders = [add_order(sync_session, today + timedelta(days=days)) for days in (-1, 0, 1, 3, 4)]
    add_order(sync_session, None)
    add_order(sync_session, today, OrderStatus.FINALIZADA)
    add_order(sync_session, today, OrderStatus.ENTREGUE)
    job = NotifyUpcomingOrdersJob(session)
    assert await job.execute(today=today, batch_size=1) == 3
    notices = sync_session.scalars(select(NotificationModel).order_by(NotificationModel.order_id)).all()
    assert [notice.order_id for notice in notices] == [order.order_id for order in orders[1:4]]
    for notice, order in zip(notices, orders[1:4]):
        assert notice.notification_id is not None
        assert notice.client_name == "Cliente Teste"
        for field in (
            "client_id", "client_email", "technical_id", "technical_name", "technical_email",
            "technical_responser_id", "technical_responser_name", "technical_responser_email",
            "vehicle_id", "service_name", "service_description", "duration_service_days",
            "order_status", "service_date_start", "service_date_end",
        ):
            assert getattr(notice, field) == getattr(order, field)
    assert await job.execute(today=today) == 0
    orders[2].service_date_end = today + timedelta(days=2)
    sync_session.commit()
    assert await job.execute(today=today) == 1


async def test_zero_days_and_default_today(job_session):
    sync_session, session = job_session
    add_order(sync_session, date.today())
    add_order(sync_session, date.today() + timedelta(days=1))
    assert await NotifyUpcomingOrdersJob(session).execute(days_before=0) == 1


async def test_failure_rolls_back_current_batch(job_session):
    sync_session, session = job_session
    add_order(sync_session, date.today())
    session.commit.side_effect = RuntimeError("commit failed")
    with pytest.raises(RuntimeError, match="commit failed"):
        await NotifyUpcomingOrdersJob(session).execute()
    session.rollback.assert_awaited_once()
    assert sync_session.scalars(select(NotificationModel)).all() == []


@pytest.mark.parametrize("options", [{"days_before": -1}, {"batch_size": 0}])
async def test_invalid_job_options(options):
    session = AsyncMock(spec=AsyncSession)
    with pytest.raises(ValueError):
        await NotifyUpcomingOrdersJob(session).execute(**options)
    session.execute.assert_not_awaited()


async def test_overdue_dates_statuses_batches_and_repeat(job_session):
    sync_session, session = job_session
    today = date(2026, 10, 25)
    overdue = [add_order(sync_session, today - timedelta(days=days)) for days in (1, 30, 300)]
    for end in (None, today, today + timedelta(days=1)):
        add_order(sync_session, end)
    for status in OrderStatus:
        if status != OrderStatus.EM_EXECUCAO:
            add_order(sync_session, today - timedelta(days=1), status)
    job = NotifyOverdueOrdersJob(session)
    assert await job.execute(today=today, batch_size=1) == 3
    notices = sync_session.scalars(select(NotificationModel).order_by(NotificationModel.order_id)).all()
    assert [notice.order_id for notice in notices] == [order.order_id for order in overdue]
    assert all(notice.notification_type == NotificationType.OVERDUE for notice in notices)
    assert await job.execute(today=today) == 0
    assert await job.execute(today=today + timedelta(days=1)) == 1  # prazo de hoje venceu
    overdue[0].service_date_end = today - timedelta(days=2)
    sync_session.commit()
    assert await job.execute(today=today) == 1


async def test_upcoming_notice_does_not_prevent_overdue_notice(job_session):
    sync_session, session = job_session
    today = date(2026, 10, 25)
    order = add_order(sync_session, today)
    upcoming = NotifyUpcomingOrdersJob(session)
    overdue = NotifyOverdueOrdersJob(session)
    assert await upcoming.execute(today=today) == 1
    assert await overdue.execute(today=today) == 0
    assert await overdue.execute(today=today + timedelta(days=1)) == 1
    assert await overdue.execute(today=today + timedelta(days=2)) == 0
    assert await upcoming.execute(today=today) == 0
    notices = sync_session.scalars(select(NotificationModel)).all()
    assert len(notices) == 2
    assert {notice.order_id for notice in notices} == {order.order_id}
    assert {notice.notification_type for notice in notices} == set(NotificationType)


async def test_overdue_uses_today_and_rolls_back_on_failure(job_session):
    sync_session, session = job_session
    add_order(sync_session, date.today() - timedelta(days=1))
    session.commit.side_effect = RuntimeError("commit failed")
    with pytest.raises(RuntimeError, match="commit failed"):
        await NotifyOverdueOrdersJob(session).execute()
    session.rollback.assert_awaited_once()
    assert sync_session.scalars(select(NotificationModel)).all() == []
    session.commit.side_effect = sync_session.commit
    assert await NotifyOverdueOrdersJob(session).execute() == 1


async def test_overdue_rejects_invalid_batch_size():
    session = AsyncMock(spec=AsyncSession)
    with pytest.raises(ValueError):
        await NotifyOverdueOrdersJob(session).execute(batch_size=0)
    session.execute.assert_not_awaited()
