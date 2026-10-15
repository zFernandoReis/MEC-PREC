from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Budget:
    
    technical_id: int
    client_id: int
    technical_name: str
    technical_disponibility: bool
    service_name: str
    amount: float
    duration_service_hours: float
    duration_service_days: int
    budget_id: int | None = None
    service_description: str | None = None
    tools: dict| None = None
    system_id: UUID = field(default_factory=uuid4)
    create_at: datetime | None = None
    update_at: datetime | None = None


