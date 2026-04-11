from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from shadowgen_application.ports import WorkerActionStorePort
from shadowgen_contracts import WorkerActionRecord, WorkerControlAction


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class CreateWorkerActionUseCase:
    worker_action_store: WorkerActionStorePort

    def execute(
        self,
        action: WorkerControlAction,
        requested_by: str,
        validation_marker: str | None = None,
        payload: dict[str, str] | None = None,
    ) -> WorkerActionRecord:
        record = WorkerActionRecord(
            command_id=str(uuid4()),
            action=action,
            requested_at=utc_now(),
            requested_by=requested_by,
            validation_marker=validation_marker,
            payload=payload or {},
        )
        return self.worker_action_store.enqueue(record)
