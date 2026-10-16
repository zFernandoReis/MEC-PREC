from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BudgetReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    technical_name: str
    technical_disponibility: bool
    service_name: str
    service_description: str | None = None
    tools: list | None = None
    amount: float
    duration_service_hours: float
    duration_service_days: int

class StockReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tool_name: str
    quantity: int
    price: float
    batch: str
    description: str | None = None
    replacement_time_hours: float | None = None
    replacement_time_days: int | None = None


class BudgetResponse(BudgetReadResponse):
    system_id: UUID


class StockCreateResponse(BaseModel):
    tool_name: str
    quantity: int
    price: float
    batch: str
    tool_id: str | None = None
    description: str | None = None
    replacement_time_hours: float | None = None
    replacement_time_days: int | None = None

class StockResponse(StockReadResponse):
    system_id: UUID

class BudgetListResponse(BudgetReadResponse):
    system_id: UUID
    budget_id: int