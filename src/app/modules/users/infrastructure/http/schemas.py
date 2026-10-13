from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
