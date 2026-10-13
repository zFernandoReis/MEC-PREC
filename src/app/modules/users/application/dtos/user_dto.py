from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.users.domain.enums.user_role import UserRole


class AddressInputDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cep: str = Field(pattern=r"^[0-9]{8}$")
    number: str = Field(min_length=1)
    complement: str | None = None


class CreateUserDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_name: str = Field(min_length=2, max_length=100)
    secondary_name: str = Field(min_length=2, max_length=100)
    cpf: str = Field(pattern=r"^[0-9]{11}$")
    email: EmailStr
    role: UserRole
    address: AddressInputDTO


class UpdateAddressDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cep: str | None = Field(
        default=None,
        pattern=r"^[0-9]{8}$"
    )
    number: str | None = Field(default=None, min_length=1)
    complement: str | None = None


class UpdateUserDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_name: str | None = Field(default=None, min_length=2, max_length=100)
    secondary_name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    role: UserRole | None = None
    address: UpdateAddressDTO | None = None
