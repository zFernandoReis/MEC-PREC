from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.users.domain.enums.fuel_type import FuelType
from app.modules.users.domain.enums.user_role import UserRole


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cep: str
    street: str
    neighborhood: str
    city: str
    state: str
    number: str | None
    complement: str | None


class UserReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    create_at: datetime
    update_at: datetime
    primary_name: str
    secondary_name: str
    cpf: str
    email: str
    role: UserRole
    address: AddressResponse = Field(validation_alias="adress")


class UserResponse(UserReadResponse):
    system_id: UUID

class VehicleReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id: int
    owner_id: int
    vehicle_type: str
    brand: str
    model: str
    year_manufacture: int
    year_model: int
    license_plate: str
    color: str
    mileage: int
    fuel_type: FuelType
    chassis: str | None = None
    engine_capacity: int | None = None
    create_at: datetime | None = None
    update_at: datetime | None = None

class VehicleResponse(VehicleReadResponse):
    system_id: UUID | None = None



