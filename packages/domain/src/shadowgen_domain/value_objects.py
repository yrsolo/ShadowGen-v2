from dataclasses import dataclass


@dataclass(slots=True)
class LegacyEndpoint:
    base_url: str
    timeout_sec: float = 120.0
