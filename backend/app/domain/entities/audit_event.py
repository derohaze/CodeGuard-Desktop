from dataclasses import dataclass, field
from datetime import datetime

from app.domain.entities.scan import utc_now


@dataclass(slots=True)
class AuditEventEntity:
    id: str
    session_id: str | None
    entity_type: str
    entity_id: str
    action: str
    payload: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
