from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Stock:
    tool_name: str
    quantity: int
    price: float
    batch: str
    tool_id: str | None = None
    description: str | None = None
    replacement_time_hours: float | None = None
    replacement_time_days: int | None = None
    system_id: UUID = field(default_factory=uuid4)
    create_at: datetime | None = None
    update_at: datetime | None = None


