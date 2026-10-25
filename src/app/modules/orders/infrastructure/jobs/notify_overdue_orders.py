from datetime import date

from app.modules.orders.domain.enums.notification_type import NotificationType
from app.modules.orders.domain.enums.order_status import OrderStatus
from app.modules.orders.infrastructure.jobs.notify_upcoming_orders import NotifyUpcomingOrdersJob
from app.modules.orders.infrastructure.models.orders_model import OrderModel


class NotifyOverdueOrdersJob(NotifyUpcomingOrdersJob):
    """Avisa uma vez por prazo vencido de uma ordem ainda em execução."""

    notification_type = NotificationType.OVERDUE

    def _deadline_conditions(self, today: date, deadline: date):
        return (
            OrderModel.service_date_end < today,
            OrderModel.order_status == OrderStatus.EM_EXECUCAO,
        )

    async def execute(self, *, batch_size: int = 100, today: date | None = None) -> int:
        return await super().execute(batch_size=batch_size, today=today, days_before=0)
