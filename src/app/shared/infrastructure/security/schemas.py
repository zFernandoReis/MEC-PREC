from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr

NewPassword = Annotated[SecretStr, Field(min_length=12, max_length=128)]
Password = Annotated[SecretStr, Field(min_length=1, max_length=128)]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cpf: str = Field(pattern=r"^[0-9]{11}$")
    password: Password


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str = Field(min_length=1, max_length=4096, repr=False)


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: Password
    new_password: NewPassword


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
