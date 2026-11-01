from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.orders.domain.entities.notification import Notification
from app.modules.orders.domain.enums.order_status import OrderStatus
from app.modules.orders.domain.enums.notification_type import NotificationType
from app.modules.orders.infrastructure.models.orders_model import OrderModel
from app.shared.infrastructure.database.base import Base


class NotificationModel(Base):
    """Persistência de Notification na tabela notifications."""

    __tablename__ = "notifications"

    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(
            NotificationType, native_enum=False, length=30,
            values_callable=lambda enum: [item.value for item in enum],
            validate_strings=True,
        ),
        default=NotificationType.UPCOMING, server_default="upcoming", nullable=False,
    )

    notification_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    system_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), default=uuid4, nullable=False, unique=True
    )
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey(OrderModel.order_id), nullable=True
    )
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    client_email: Mapped[str] = mapped_column(String(254), nullable=False)
    client_name: Mapped[str] = mapped_column(String(100), nullable=False)
    technical_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    technical_name: Mapped[str] = mapped_column(String(100), nullable=False)
    technical_email: Mapped[str] = mapped_column(String(254), nullable=False)
    technical_responser_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    technical_responser_name: Mapped[str] = mapped_column(String(100), nullable=False)
    technical_responser_email: Mapped[str] = mapped_column(String(254), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.vehicle_id"), nullable=False)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
    def from_entity(cls, notification: Notification) -> "NotificationModel":
        return cls(
            notification_type=notification.notification_type,
            notification_id=notification.notification_id,
            system_id=notification.system_id,
            order_id=notification.order_id,
            client_id=notification.client_id,
            client_email=notification.client_email,
            client_name=notification.client_name,
            technical_id=notification.technical_id,
            technical_name=notification.technical_name,
            technical_email=notification.technical_email,
            technical_responser_id=notification.technical_responser_id,
            technical_responser_name=notification.technical_responser_name,
            technical_responser_email=notification.technical_responser_email,
            vehicle_id=notification.vehicle_id,
            service_name=notification.service_name,
            service_description=notification.service_description,
            duration_service_days=notification.duration_service_days,
            order_status=notification.order_status,
            service_date_start=notification.service_date_start,
            service_date_end=notification.service_date_end,
            create_at=notification.create_at,
            update_at=notification.update_at,
        )

    def to_entity(self) -> Notification:
        return Notification(
            notification_type=self.notification_type,
            notification_id=self.notification_id,
            system_id=self.system_id,
            order_id=self.order_id,
            client_id=self.client_id,
            client_email=self.client_email,
            client_name=self.client_name,
            technical_id=self.technical_id,
            technical_name=self.technical_name,
            technical_email=self.technical_email,
            technical_responser_id=self.technical_responser_id,
            technical_responser_name=self.technical_responser_name,
            technical_responser_email=self.technical_responser_email,
            vehicle_id=self.vehicle_id,
            service_name=self.service_name,
            service_description=self.service_description,
            duration_service_days=self.duration_service_days,
            order_status=self.order_status,
            service_date_start=self.service_date_start,
            service_date_end=self.service_date_end,
            create_at=self.create_at,
            update_at=self.update_at,
        )
