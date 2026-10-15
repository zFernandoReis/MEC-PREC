from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Identity, Integer, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.budgets.domain.entities.budget import Budget
from app.shared.infrastructure.database.base import Base


class BudgetModel(Base):
    """Persistência de Budget na tabela budgets."""

    __tablename__ = "budgets"

    system_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), default=uuid4, nullable=False, unique=True
    )
    budget_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    technical_id: Mapped[int] = mapped_column(Integer, nullable=False)
    client_id: Mapped[int] = mapped_column(Integer, nullable=False)
    technical_name: Mapped[str] = mapped_column(String(100), nullable=False)
    technical_disponibility: Mapped[bool] = mapped_column(nullable=False)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tools: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    amount: Mapped[float] = mapped_column(nullable=False)
    duration_service_hours: Mapped[float] = mapped_column(nullable=False)
    duration_service_days: Mapped[int] = mapped_column(nullable=False)
    create_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    update_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )

    @classmethod
    def from_entity(cls, budget: Budget) -> "BudgetModel":
        return cls(
            system_id=budget.system_id,
            budget_id=budget.budget_id,
            technical_id=budget.technical_id,
            client_id=budget.client_id,
            technical_name=budget.technical_name,
            technical_disponibility=budget.technical_disponibility,
            service_name=budget.service_name,
            service_description=budget.service_description,
            tools=budget.tools,
            amount=budget.amount,
            duration_service_hours=budget.duration_service_hours,
            duration_service_days=budget.duration_service_days,
        )

    def to_entity(self) -> Budget:
        return Budget(
            system_id=self.system_id,
            budget_id=self.budget_id,
            technical_id=self.technical_id,
            client_id=self.client_id,
            technical_name=self.technical_name,
            technical_disponibility=self.technical_disponibility,
            service_name=self.service_name,
            service_description=self.service_description,
            tools=self.tools,
            amount=self.amount,
            duration_service_hours=self.duration_service_hours,
            duration_service_days=self.duration_service_days,
)
