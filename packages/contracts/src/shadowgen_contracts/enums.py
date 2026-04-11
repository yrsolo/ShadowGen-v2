from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class OutputFormat(str, Enum):
    PNG = "png"
    JPEG = "jpeg"


class BackgroundMode(str, Enum):
    SOLID = "solid"
    TRANSPARENT = "transparent"


class AssetKind(str, Enum):
    SOURCE = "source"
    FINAL = "final"
    DEBUG = "debug"
