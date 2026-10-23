from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Identity, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.orders.domain.entities.orders import Order
from app.modules.orders.domain.enums.order_status import OrderStatus
from app.modules.quotes.infrastructure.models.budgets_model import BudgetModel
from app.modules.users.infrastructure.models.users_model import UserModel
from app.modules.users.infrastructure.models.vehicles_model import VehicleModel
from app.shared.infrastructure.database.base import Base


class OrderModel(Base):
    """Persistência de Order na tabela orders."""

    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    system_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), default=uuid4, nullable=False, unique=True
    )
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    technical_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    technical_responser_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.vehicle_id"), nullable=False)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budgets.budget_id"), nullable=False)

    client: Mapped[UserModel] = relationship(foreign_keys=[client_id])
    technical: Mapped[UserModel] = relationship(foreign_keys=[technical_id])
    technical_responser: Mapped[UserModel] = relationship(
        foreign_keys=[technical_responser_id]
    )
    vehicle: Mapped[VehicleModel] = relationship()
    budget: Mapped[BudgetModel] = relationship()

    client_email: Mapped[str] = mapped_column(String(254), nullable=False)
    technical_name: Mapped[str] = mapped_column(String(100), nullable=False)
    technical_email: Mapped[str] = mapped_column(String(254), nullable=False)
    technical_responser_name: Mapped[str] = mapped_column(String(100), nullable=False)
    technical_responser_email: Mapped[str] = mapped_column(String(254), nullable=False)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration_service_hours: Mapped[float] = mapped_column(nullable=False)
    duration_service_days: Mapped[int | None] = mapped_column(nullable=True)
    order_status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            name="order_status",
            values_callable=lambda enum: [item.value for item in enum],
            validate_strings=True,
        ),
        nullable=False,
    )
    service_date_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    service_date_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    create_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    update_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )

    @classmethod
    def from_entity(cls, order: Order) -> "OrderModel":
        return cls(
            order_id=order.order_id,
            system_id=order.system_id,
            client_id=order.client_id,
            client_email=order.client_email,
            technical_id=order.technical_id,
            technical_name=order.technical_name,
            technical_email=order.technical_email,
            technical_responser_id=order.technical_responser_id,
            technical_responser_name=order.technical_responser_name,
            technical_responser_email=order.technical_responser_email,
            budget_id=order.budget_id,
            vehicle_id=order.vehicle_id,
            service_name=order.service_name,
            service_description=order.service_description,
            duration_service_hours=order.duration_service_hours,
            duration_service_days=order.duration_service_days,
            order_status=order.order_status,
            service_date_start=order.service_date_start,
            service_date_end=order.service_date_end,
            create_at=order.create_at,
            update_at=order.update_at,
        )

    def to_entity(self) -> Order:
        return Order(
            order_id=self.order_id,
            system_id=self.system_id,
            client_id=self.client_id,
            client_email=self.client_email,
            technical_id=self.technical_id,
            technical_name=self.technical_name,
            technical_email=self.technical_email,
            technical_responser_id=self.technical_responser_id,
            technical_responser_name=self.technical_responser_name,
            technical_responser_email=self.technical_responser_email,
            budget_id=self.budget_id,
            vehicle_id=self.vehicle_id,
            service_name=self.service_name,
            service_description=self.service_description,
            duration_service_hours=self.duration_service_hours,
            duration_service_days=self.duration_service_days,
            order_status=self.order_status,
            service_date_start=self.service_date_start,
            service_date_end=self.service_date_end,
            create_at=self.create_at,
            update_at=self.update_at,
        )
