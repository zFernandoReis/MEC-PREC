from dataclasses import field
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict

from app.modules.orders.domain.enums.order_status import OrderStatus


class OrdersReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    client_id: int
    client_email: str
    technical_id: int
    technical_name: str
    technical_email: str
    budget_id: int
    vehicle_id: int
    service_name: str
    technical_responser_id: int
    technical_responser_name: str
    technical_responser_email: str
    duration_service_days: int
    duration_service_hours: float
    order_status: OrderStatus
    service_date_start: datetime | None = None
    service_date_end: datetime | None = None
    order_id: int | None = None
    service_description: str | None = None
    system_id: UUID = field(default_factory=uuid4)
    create_at: datetime | None = None
    update_at: datetime | None = None



class OrdersResponse(OrdersReadResponse):
    system_id: UUID


