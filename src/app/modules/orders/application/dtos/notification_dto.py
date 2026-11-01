from datetime import date

from pydantic import BaseModel, ConfigDict

from app.modules.orders.domain.enums.order_status import OrderStatus
from app.modules.orders.domain.enums.notification_type import NotificationType


class CreateNotificationDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: int
    client_email: str
    client_name: str
    technical_id: int
    technical_name: str
    technical_email: str
    vehicle_id: int
    service_name: str
    technical_responser_id: int
    technical_responser_name: str
    technical_responser_email: str
    order_status: OrderStatus
    service_date_start: date | None = None
    service_date_end: date | None = None
    order_id: int | None = None
    service_description: str | None = None
    duration_service_days: int | None = None
    notification_type: NotificationType = NotificationType.UPCOMING
