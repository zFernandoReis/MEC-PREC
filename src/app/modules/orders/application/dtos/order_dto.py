from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class CreateOrderDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: int
    client_email: str
    technical_id: int
    technical_name: str
    technical_email: str
    budget_id: int
    vehicle_id: int
    service_name: str
    technical_responser_id: int
    technical_responser_name: str
    technical_responser_email: str
    
    duration_service_hours: float = Field(gt=0, allow_inf_nan=False)
    service_description: str | None = None

class UpdateOrderDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: int | None = None
    client_email: str | None = None
    technical_id: int | None = None
    technical_name: str | None = None
    technical_email: str | None = None
    budget_id: int | None = None
    vehicle_id: int | None = None
    service_name: str | None = None
    technical_responser_id: int | None = None
    technical_responser_name: str | None = None
    technical_responser_email: str | None = None
    duration_service_days: int | None = None
    duration_service_hours: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    service_description: str | None = None

    @field_validator("*")
    @classmethod
    def reject_null_required_fields(cls, value, info: ValidationInfo):
        # Campos omitidos não são validados nem aplicados pelo PATCH.
        if value is None and info.field_name not in {"service_description", "duration_service_days"}:
            raise ValueError("O campo não pode ser nulo; omita-o para preservar o valor atual")
        return value
