from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.domain.entities.notification import Notification
from app.modules.orders.domain.enums.order_status import OrderStatus
from app.modules.orders.domain.enums.notification_type import NotificationType
from app.modules.orders.infrastructure.models.notification_model import NotificationModel
from app.modules.orders.infrastructure.models.orders_model import OrderModel
from app.modules.users.infrastructure.models.users_model import UserModel
from app.shared.infrastructure.logging import logger


class NotifyUpcomingOrdersJob:
    """Cria um aviso por ordem e prazo, confirmando cada lote em uma transação."""

    notification_type = NotificationType.UPCOMING

    def _deadline_conditions(self, today: date, deadline: date):
        return (
            OrderModel.service_date_end >= today,
            OrderModel.service_date_end <= deadline,
            OrderModel.order_status.not_in([OrderStatus.FINALIZADA, OrderStatus.ENTREGUE]),
        )

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(
        self, *, days_before: int = 3, batch_size: int = 100, today: date | None = None
    ) -> int:
        if days_before < 0 or batch_size < 1:
            raise ValueError("days_before deve ser >= 0 e batch_size deve ser >= 1")
        today = today if today is not None else date.today()
        deadline = today + timedelta(days=days_before)
        last_id = 0
        created = 0
        try:
            while True:
                already_notified = select(NotificationModel.notification_id).where(
                    NotificationModel.order_id == OrderModel.order_id,
                    NotificationModel.service_date_end == OrderModel.service_date_end,
                    NotificationModel.notification_type == self.notification_type,
                ).exists()
                result = await self.session.execute(
                    select(OrderModel, UserModel.primary_name, UserModel.secondary_name)
                    .join(UserModel, UserModel.id == OrderModel.client_id)
                    .where(
                        OrderModel.order_id > last_id,
                        *self._deadline_conditions(today, deadline),
                        ~already_notified,
                    )
                    .order_by(OrderModel.order_id)
                    .limit(batch_size)
                    .with_for_update(of=OrderModel, skip_locked=True)
                )
                rows = result.all()
                if not rows:
                    await self.session.commit()
                    break
                # Revalida após adquirir os locks: outra execução pode ter
                # confirmado um aviso desde o início da consulta do lote.
                existing = await self.session.execute(
                    select(NotificationModel.order_id, NotificationModel.service_date_end)
                    .where(
                        NotificationModel.order_id.in_([row[0].order_id for row in rows]),
                        NotificationModel.notification_type == self.notification_type,
                    )
                )
                notified = set(existing.all())
                batch_created = 0
                for order, primary_name, secondary_name in rows:
                    if (order.order_id, order.service_date_end) in notified:
                        continue
                    notification = Notification(
                        notification_type=self.notification_type,
                        order_id=order.order_id,
                        client_id=order.client_id,
                        client_email=order.client_email,
                        client_name=f"{primary_name} {secondary_name}".strip(),
                        technical_id=order.technical_id,
                        technical_name=order.technical_name,
                        technical_email=order.technical_email,
                        technical_responser_id=order.technical_responser_id,
                        technical_responser_name=order.technical_responser_name,
                        technical_responser_email=order.technical_responser_email,
                        vehicle_id=order.vehicle_id,
                        service_name=order.service_name,
                        service_description=order.service_description,
                        service_date_start=order.service_date_start,
                        service_date_end=order.service_date_end,
                        duration_service_days=order.duration_service_days,
                        order_status=order.order_status,
                    )
                    self.session.add(NotificationModel.from_entity(notification))
                    batch_created += 1
                last_id = rows[-1][0].order_id
                await self.session.commit()
                created += batch_created
        except Exception:
            await self.session.rollback()
            raise
        logger.info(
            "Varredura de prazos concluída: notification_type=%s, notifications_created=%s",
            self.notification_type, created,
        )
        return created
