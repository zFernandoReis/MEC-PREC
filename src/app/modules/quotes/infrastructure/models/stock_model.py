from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.quotes.domain.entities.stock import Stock
from app.shared.infrastructure.database.base import Base


class StockModel(Base):
    """Persistência de Stock na tabela stock."""

    __tablename__ = "stock"

    system_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), default=uuid4, nullable=False, unique=True
    )
    tool_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(nullable=False)
    batch: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    replacement_time_hours: Mapped[float] = mapped_column(nullable=False)
    replacement_time_days: Mapped[int] = mapped_column(nullable=False)
    create_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    update_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )

    @classmethod
    def from_entity(cls, stock: Stock) -> "StockModel":
        return cls(
            system_id=stock.system_id,
            tool_id=stock.tool_id,
            tool_name=stock.tool_name,
            price=stock.price,
            batch=stock.batch,
            description=stock.description,
            quantity=stock.quantity,
            replacement_time_hours=stock.replacement_time_hours,
            replacement_time_days=stock.replacement_time_days,
        )

    def to_entity(self) -> Stock:
        return Stock(
            system_id=self.system_id,
            tool_id=self.tool_id,
            tool_name=self.tool_name,
            price=self.price,
            batch=self.batch,
            description=self.description,
            quantity=self.quantity,
            replacement_time_hours=self.replacement_time_hours,
            replacement_time_days=self.replacement_time_days,
        )
