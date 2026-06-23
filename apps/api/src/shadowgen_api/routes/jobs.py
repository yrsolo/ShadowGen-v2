from fastapi import APIRouter, Depends, HTTPException

from shadowgen_application.dto import CreateJobCommand
from shadowgen_application.ports import AssetStorePort
from shadowgen_application.use_cases.create_job import CreateJobUseCase
from shadowgen_application.use_cases.get_job import GetJobUseCase
from shadowgen_application.use_cases.get_job_result import GetJobResultUseCase
from shadowgen_application.use_cases.manage_job import ManageJobUseCase
from shadowgen_contracts import (
    ClearJobCacheResponse,
    CreateJobRequest,
    CreateJobResponse,
    GetJobResponse,
    GetJobResultResponse,
    JobMutationResponse,
    MarkJobFailedRequest,
    derive_job_timing_metrics,
)
from shadowgen_domain import AssetNotFoundError, JobNotFoundError

from shadowgen_api.deps import (
    get_asset_store,
    get_create_job_use_case,
    get_get_job_result_use_case,
    get_get_job_use_case,
    get_manage_job_use_case,
    get_realtime_accelerator,
    require_admin_token,
)

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.post("", response_model=CreateJobResponse)
def create_job(
    payload: CreateJobRequest,
    use_case: CreateJobUseCase = Depends(get_create_job_use_case),
    asset_store: AssetStorePort = Depends(get_asset_store),
    realtime_accelerator=Depends(get_realtime_accelerator),
):
    try:
        source_hash = asset_store.get_source_hash(payload.render.source_asset_id)
    except AssetNotFoundError:
        raise HTTPException(status_code=400, detail="Source asset does not exist.")

    job = use_case.execute(CreateJobCommand(request=payload.render, source_hash=source_hash))
    realtime = realtime_accelerator.subscription_for_job(job.job_id)
    try:
        realtime_accelerator.notify_job_queued(job)
    except Exception:
        pass
    if job.status.value in {"succeeded", "failed", "canceled"}:
        realtime = None
    return CreateJobResponse(
        job_id=job.job_id,
        status=job.status,
        cache_status=job.cache_status,
        reused_existing_job=job.reused_existing_job,
        job=job,
        timing=derive_job_timing_metrics(job),
        realtime=realtime,
    )


@router.get("/{job_id}", response_model=GetJobResponse)
def get_job(
    job_id: str,
    use_case: GetJobUseCase = Depends(get_get_job_use_case),
    realtime_accelerator=Depends(get_realtime_accelerator),
):
    try:
        job = use_case.execute(job_id)
        realtime = None if job.status.value in {"succeeded", "failed", "canceled"} else realtime_accelerator.subscription_for_job(job.job_id)
        return GetJobResponse(job=job, timing=derive_job_timing_metrics(job), realtime=realtime)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{job_id}/result", response_model=GetJobResultResponse)
def get_job_result(job_id: str, use_case: GetJobResultUseCase = Depends(get_get_job_result_use_case)):
    try:
        job = use_case.execute(job_id)
        return GetJobResultResponse(job_id=job.job_id, status=job.status, result=job.result)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/cache/clear", response_model=ClearJobCacheResponse)
def clear_job_cache(
    _admin: None = Depends(require_admin_token),
    use_case: ManageJobUseCase = Depends(get_manage_job_use_case),
) -> ClearJobCacheResponse:
    cleared_entries = use_case.clear_request_cache()
    return ClearJobCacheResponse(cleared_entries=cleared_entries)


@router.post("/{job_id}/mark-failed", response_model=JobMutationResponse)
def mark_job_failed(
    job_id: str,
    payload: MarkJobFailedRequest,
    _admin: None = Depends(require_admin_token),
    use_case: ManageJobUseCase = Depends(get_manage_job_use_case),
) -> JobMutationResponse:
    try:
        job = use_case.mark_failed(job_id=job_id, reason=payload.reason)
        return JobMutationResponse(job_id=job.job_id, status=job.status, deleted=False)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{job_id}", response_model=JobMutationResponse)
def delete_job(
    job_id: str,
    _admin: None = Depends(require_admin_token),
    use_case: ManageJobUseCase = Depends(get_manage_job_use_case),
) -> JobMutationResponse:
    try:
        use_case.delete(job_id)
        return JobMutationResponse(job_id=job_id, deleted=True)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
