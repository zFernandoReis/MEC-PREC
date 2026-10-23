from pydantic import BaseModel, ConfigDict, Field


class BudgetToolDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_id: str = Field(min_length=1, max_length=100)
    tool_name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0)


class CreateBudgetDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    technical_id: int
    client_id: int
    vehicle_id: int = Field(gt=0)
    technical_name: str
    technical_disponibility: bool
    service_name: str
    service_description: str | None = None
    tools: list[BudgetToolDTO] | None = None
    amount: float
    duration_service_hours: float
    duration_service_days: int


class UpdateBudgetDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    technical_name: str
    technical_disponibility: bool
    service_name: str
    service_description: str | None = None
    tools: list[BudgetToolDTO] | None = None
    amount: float
    duration_service_hours: float
    duration_service_days: int
