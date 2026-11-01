from dataclasses import asdict
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Identity, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.orders.domain.entities.order_event import OrderEvent
from app.shared.infrastructure.database.base import Base


class OrderEventModel(Base):
    __tablename__ = "order_events"
    __table_args__ = (UniqueConstraint("order_id", "version", name="uq_order_event_version"),)

    event_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    previous_status: Mapped[str] = mapped_column(String(40), nullable=False)
    next_status: Mapped[str] = mapped_column(String(40), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False)

    @classmethod
    def from_entity(cls, event: OrderEvent):
        return cls(**asdict(event))

    def to_entity(self):
        return OrderEvent(**{name: getattr(self, name) for name in OrderEvent.__dataclass_fields__})
