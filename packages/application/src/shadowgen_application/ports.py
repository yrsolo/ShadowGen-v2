from typing import Protocol

from shadowgen_contracts import (
    AssetKind,
    AssetRef,
    JobRecord,
    LocalRuntimeConfig,
    QueueDiagnostics,
    RenderJobQueuedMessage,
    WorkerActionRecord,
    WorkerCapabilitySnapshot,
    WorkerInFlightJob,
    WorkerRuntimeState,
)
from shadowgen_pipeline import PipelineCapabilitiesSummary, PipelineContext, PipelinePollResult, PipelineSubmission


class JobRepositoryPort(Protocol):
    def create(self, job: JobRecord) -> None:
        ...

    def get(self, job_id: str) -> JobRecord | None:
        ...

    def update(self, job: JobRecord) -> None:
        ...

    def delete(self, job: JobRecord) -> None:
        ...

    def find_by_request_cache_key(self, cache_key: str) -> JobRecord | None:
        ...

    def list_recent(self, limit: int = 20) -> list[JobRecord]:
        ...


class JobQueuePublisherPort(Protocol):
    def publish(self, message: RenderJobQueuedMessage) -> None:
        ...


class JobQueueConsumerPort(Protocol):
    def receive(self) -> "QueueDeliveryPort | None":
        ...


class QueueDeliveryPort(Protocol):
    message: RenderJobQueuedMessage

    def ack(self) -> None:
        ...

    def nack(self) -> None:
        ...

    def extend_visibility(self, timeout_sec: int) -> None:
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

    def get_source_hash(self, asset_id: str) -> str:
        ...


class RenderPipelinePort(Protocol):
    def probe(self, force_refresh: bool = False) -> PipelineCapabilitiesSummary:
        ...

    def submit(self, context: PipelineContext) -> PipelineSubmission:
        ...

    def poll(self, submission: PipelineSubmission) -> PipelinePollResult:
        ...

    def cancel(self, submission: PipelineSubmission) -> None:
        ...


class ProcessJobObserverPort(Protocol):
    def capabilities_refreshed(self, snapshot: WorkerCapabilitySnapshot) -> None:
        ...

    def job_submitted(self, state: WorkerInFlightJob) -> None:
        ...

    def job_polled(self, state: WorkerInFlightJob) -> None:
        ...

    def job_finished(self, job: JobRecord) -> None:
        ...

    def job_failed(self, job_id: str, error_text: str, failure_stage: str | None = None) -> None:
        ...
