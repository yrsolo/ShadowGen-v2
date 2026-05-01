from dataclasses import dataclass

from shadowgen_contracts import RenderRequest


@dataclass(slots=True)
class CreateJobCommand:
    request: RenderRequest
    source_hash: str | None = None
