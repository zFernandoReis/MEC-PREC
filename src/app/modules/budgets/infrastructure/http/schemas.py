from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BudgetReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    technical_name: str
    technical_disponibility: bool
    service_name: str
    service_description: str | None = None
    tools: dict[str, int] | None = None
    amount: float
    duration_service_hours: float
    duration_service_days: int

class BudgetResponse(BudgetReadResponse):
    system_id: UUID
