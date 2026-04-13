from dataclasses import dataclass, field
from datetime import datetime

from app.domain.entities.scan import utc_now


@dataclass(slots=True)
class VerificationRunEntity:
    id: str
    session_id: str
    finding_id: str
    fix_id: str
    status: str
    checks: list[str] = field(default_factory=list)
    logs_ref: str | None = None
    payload: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
