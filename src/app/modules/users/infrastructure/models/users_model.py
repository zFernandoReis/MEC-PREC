from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Identity, Integer, String, Uuid, func, text
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from app.modules.quotes.infrastructure.models.budgets_model import BudgetModel
from app.modules.users.domain.entities.user import User
from app.modules.users.domain.enums.user_role import UserRole
from app.modules.users.domain.value_objects.address import Address
from app.modules.users.infrastructure.models.vehicles_model import VehicleModel
from app.shared.infrastructure.database.base import Base


class UserModel(Base):
    """Persistência de User na tabela users, incluindo apenas o hash da senha."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    vehicles: Mapped[list[VehicleModel]] = relationship(back_populates="owner")
    technical_budgets: Mapped[list[BudgetModel]] = relationship(
        foreign_keys=[BudgetModel.technical_id], back_populates="technical",
    )
    client_budgets: Mapped[list[BudgetModel]] = relationship(
        foreign_keys=[BudgetModel.client_id], back_populates="client",
    )
    system_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), default=uuid4, nullable=False, unique=True
    )
    create_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    update_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )
    primary_name: Mapped[str] = mapped_column(String(100), nullable=False)
    secondary_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    # Registros legados sem senha ficam impedidos de fazer login até a definição.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0"),
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=lambda enum: [item.value for item in enum],
            validate_strings=True,
        ),
        nullable=False,
    )

    cep: Mapped[str] = mapped_column(String(8), nullable=False)
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    neighborhood: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    complement: Mapped[str | None] = mapped_column(String(255), nullable=True)

    address: Mapped[Address] = composite(
        Address, "cep", "street", "neighborhood", "city", "state",
        "number", "complement",
    )

    @classmethod
    def from_entity(cls, user: User) -> "UserModel":
        return cls(
            id=user.id,
            system_id=user.system_id,
            primary_name=user.primary_name,
            secondary_name=user.secondary_name,
            cpf=user.cpf,
            email=user.email,
            role=user.role,
            address=user.adress,
            password_hash=user.password_hash,
            token_version=user.token_version,
        )

    def to_entity(self) -> User:
        return User(
            id=self.id,
            system_id=self.system_id,
            create_at=self.create_at,
            update_at=self.update_at,
            primary_name=self.primary_name,
            secondary_name=self.secondary_name,
            cpf=self.cpf,
            email=self.email,
            role=self.role,
            adress=self.address,
            password_hash=self.password_hash,
            token_version=self.token_version,
        )
