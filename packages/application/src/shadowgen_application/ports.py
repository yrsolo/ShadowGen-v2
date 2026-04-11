from typing import Protocol

from shadowgen_contracts import (
    AssetKind,
    AssetRef,
    JobRecord,
    LocalRuntimeConfig,
    QueueDiagnostics,
    RenderJobQueuedMessage,
    WorkerActionRecord,
    WorkerRuntimeState,
)
from shadowgen_pipeline import PipelineContext, PipelineOutput


class JobRepositoryPort(Protocol):
    def create(self, job: JobRecord) -> None:
        ...

    def get(self, job_id: str) -> JobRecord | None:
        ...

    def update(self, job: JobRecord) -> None:
        ...

    def list_recent(self, limit: int = 20) -> list[JobRecord]:
        ...


class JobQueuePublisherPort(Protocol):
    def publish(self, message: RenderJobQueuedMessage) -> None:
        ...


class JobQueueConsumerPort(Protocol):
    def consume(self) -> RenderJobQueuedMessage | None:
        ...


class QueueInspectorPort(Protocol):
    def diagnostics(self) -> QueueDiagnostics:
        ...


class RuntimeConfigStorePort(Protocol):
    def get(self) -> LocalRuntimeConfig:
        ...

    def update(self, config: LocalRuntimeConfig) -> LocalRuntimeConfig:
        ...


class WorkerStateStorePort(Protocol):
    def get(self) -> WorkerRuntimeState:
        ...

    def update(self, state: WorkerRuntimeState) -> WorkerRuntimeState:
        ...


class WorkerActionStorePort(Protocol):
    def enqueue(self, action: WorkerActionRecord) -> WorkerActionRecord:
        ...

    def take_next(self) -> WorkerActionRecord | None:
        ...

    def update(self, action: WorkerActionRecord) -> WorkerActionRecord:
        ...

    def list_recent(self, limit: int = 20) -> list[WorkerActionRecord]:
        ...


class AssetStorePort(Protocol):
    def put_bytes(self, data: bytes, kind: AssetKind, mime_type: str) -> AssetRef:
        ...

    def get_bytes(self, asset_id: str) -> bytes:
        ...

    def get_ref(self, asset_id: str) -> AssetRef | None:
        ...


class RenderPipelinePort(Protocol):
    def render(self, context: PipelineContext) -> PipelineOutput:
        ...
