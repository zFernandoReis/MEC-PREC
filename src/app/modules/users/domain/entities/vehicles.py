from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.users.domain.enums.fuel_type import FuelType
from app.modules.users.domain.enums.vehicles_type import VehicleType


@dataclass
class Vehicle:
    
    owner_id: int
    vehicle_type: VehicleType
    brand: str
    model: str
    year_manufacture: int
    year_model: int
    license_plate: str
    color: str
    mileage: int
    fuel_type: FuelType
    vehicle_id: int | None = None
    chassis: str | None = None
    engine_capacity: int | None = None
    system_id: UUID | None = None
    create_at: datetime | None = None
    update_at: datetime | None = None

    def __post_init__(self):
        self.validate_license_plate()
        self.validate_year()
        self.validate_mileage()
        self.validate_engine_capacity()

    def validate_license_plate(self):
        plate = self.license_plate.replace("-", "").upper()

        if len(plate) != 7 or not plate.isascii() or not plate.isalnum():
            raise ValueError("Placa inválida")

        self.license_plate = plate

    def validate_year(self):
        current_year = datetime.now().year

        if not 1886 <= self.year_manufacture <= current_year + 1:
            raise ValueError("Ano de fabricação inválido")

        if not 1886 <= self.year_model <= current_year + 1:
            raise ValueError("Ano do modelo inválido")

    def validate_mileage(self):
        if self.mileage < 0:
            raise ValueError("Quilometragem não pode ser negativa")

    def validate_engine_capacity(self):
        if self.engine_capacity is not None and self.engine_capacity <= 0:
            raise ValueError("Cilindrada deve ser maior que zero")

    def update_mileage(self, new_mileage: int):
        if new_mileage < self.mileage:
            raise ValueError(
                "Nova quilometragem não pode ser menor que a atual"
            )

        self.mileage = new_mileage