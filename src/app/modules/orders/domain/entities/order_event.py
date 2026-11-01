from dataclasses import dataclass
from datetime import datetime


@dataclass
class OrderEvent:
    order_id: int
    action: str
    previous_status: str
    next_status: str
    version: int
    actor_id: int
    occurred_at: datetime
    details: dict
    event_id: int | None = None
