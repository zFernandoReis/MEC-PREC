from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Stock:
    system_id: UUID = field(default_factory=uuid4)
    tool_id: int | None
    name: str
    description: str | None = None
    quantity: int
    price: float
    batch: str | None = None
    replacement_time_hours: float | None = None
    replacement_time_days: int | None = None


