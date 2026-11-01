from pydantic import BaseModel, ConfigDict


class CreateStockDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str
    quantity: int
    price: float
    batch: str
    replacement_time_hours: float
    replacement_time_days: int
    tool_description: str | None = None


class UpdateStockDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: str | None = None
    quantity: int | None = None
    price: float | None = None
    batch: str | None = None
    replacement_time_hours: float | None = None
    replacement_time_days: int | None = None
    tool_description: str | None = None