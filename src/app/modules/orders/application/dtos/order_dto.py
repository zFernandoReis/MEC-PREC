from pydantic import BaseModel, ConfigDict

from app.modules.orders.domain.enums.order_status import OrderStatus


class CreateOrderDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    
    duration_service_hours: float
    order_status: OrderStatus
    service_description: str | None = None

class UpdateOrderDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    service_description: str | None = None