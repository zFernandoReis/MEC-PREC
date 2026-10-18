from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Identity, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.users.domain.entities.vehicles import Vehicle
from app.modules.users.domain.enums.fuel_type import FuelType
from app.modules.users.domain.enums.vehicles_type import VehicleType
from app.shared.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.modules.quotes.infrastructure.models.budgets_model import BudgetModel
    from app.modules.users.infrastructure.models.users_model import UserModel


class VehicleModel(Base):
    """Persistência de Vehicle na tabela veiculos."""

    __tablename__ = "vehicles"

    vehicle_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped["UserModel"] = relationship(back_populates="vehicles")
    budgets: Mapped[list["BudgetModel"]] = relationship(back_populates="vehicle")
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
    vehicle_type: Mapped[VehicleType] = mapped_column(
        Enum(
            VehicleType,
            name="vehicle_type",
            values_callable=lambda enum: [item.value for item in enum],
            validate_strings=True,
        ),
        nullable=False,
    )
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year_manufacture: Mapped[int] = mapped_column(Integer, nullable=False)
    year_model: Mapped[int] = mapped_column(Integer, nullable=False)
    license_plate: Mapped[str] = mapped_column(String(7), nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String(100), nullable=False)
    mileage: Mapped[int] = mapped_column(Integer, nullable=False)
    fuel_type: Mapped[FuelType] = mapped_column(
        Enum(
            FuelType,
            name="fuel_type",
            values_callable=lambda enum: [item.value for item in enum],
            validate_strings=True,
        ),
        nullable=False,
    )
    chassis: Mapped[str | None] = mapped_column(String(17), nullable=True)
    engine_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)      

    @classmethod
    def from_entity(cls, vehicle: Vehicle) -> "VehicleModel":
        return cls(
            vehicle_id=vehicle.vehicle_id,
            system_id=vehicle.system_id,
            owner_id=vehicle.owner_id,
            vehicle_type=vehicle.vehicle_type,
            brand=vehicle.brand,
            model=vehicle.model,
            year_manufacture=vehicle.year_manufacture,
            year_model=vehicle.year_model,
            license_plate=vehicle.license_plate,
            color=vehicle.color,
            mileage=vehicle.mileage,
            fuel_type=vehicle.fuel_type,
            chassis=vehicle.chassis,
            engine_capacity=vehicle.engine_capacity,

        )

    def to_entity(self) -> Vehicle:
        return Vehicle(
            vehicle_id=self.vehicle_id,
            system_id=self.system_id,
            create_at=self.create_at,
            update_at=self.update_at,
            vehicle_type=self.vehicle_type,
            owner_id=self.owner_id,
            brand=self.brand,
            model=self.model,
            year_manufacture=self.year_manufacture,
            year_model=self.year_model,
            license_plate=self.license_plate,
            color=self.color,
            mileage=self.mileage,
            fuel_type=self.fuel_type,
            chassis=self.chassis,
            engine_capacity=self.engine_capacity,
        )
