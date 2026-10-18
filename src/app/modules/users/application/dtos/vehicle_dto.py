import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateVehicleDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_id: int = Field(gt=0)
    vehicle_type: str = Field(min_length=2, max_length=100)
    brand: str = Field(min_length=2, max_length=100)
    model: str = Field(min_length=2, max_length=100)
    year_manufacture: int = Field(gt=1886, le=datetime.datetime.now().year + 1)
    year_model: int = Field(gt=1886, le=datetime.datetime.now().year + 1)
    license_plate: str = Field(pattern=r"^[A-Z]{3}[0-9]{4}$")
    color: str = Field(min_length=2, max_length=50)
    mileage: int = Field(ge=0)
    fuel_type: str = Field(min_length=2, max_length=50)
    chassis: str | None = Field(default=None, min_length=13, max_length=17)
    engine_capacity: int | None = Field(default=None, gt=0)




class UpdateVehicleDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_type: str | None = Field(default=None, min_length=2, max_length=100)
    brand: str | None = Field(default=None, min_length=2, max_length=100)
    model: str | None = Field(default=None, min_length=2, max_length=100)
    year_manufacture: int | None = Field(default=None, gt=1886, le=datetime.datetime.now().year + 1)
    year_model: int | None = Field(default=None, gt=1886, le=datetime.datetime.now().year + 1)
    license_plate: str | None = Field(default=None, pattern=r"^[A-Z]{3}[0-9]{4}$")
    color: str | None = Field(default=None, min_length=2, max_length=50)
    mileage: int | None = Field(default=None, ge=0)
    fuel_type: str | None = Field(default=None, min_length=2, max_length=50)
    chassis: str | None = Field(default=None, min_length=13, max_length=17)
    engine_capacity: int | None = Field(default=None, gt=0)