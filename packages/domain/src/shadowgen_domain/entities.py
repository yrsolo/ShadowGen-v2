from dataclasses import dataclass
from datetime import datetime

from shadowgen_contracts import JobStatus, RenderRequest, RenderResult


@dataclass(slots=True)
class JobEntity:
    job_id: str
    status: JobStatus
    request: RenderRequest
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: RenderResult | None = None
