from fastapi import APIRouter, Depends

from shadowgen_application.use_cases.get_runtime_config import GetRuntimeConfigUseCase
from shadowgen_application.use_cases.get_system_diagnostics import GetSystemDiagnosticsUseCase
from shadowgen_application.use_cases.update_runtime_config import UpdateRuntimeConfigUseCase
from shadowgen_application.use_cases.create_worker_action import CreateWorkerActionUseCase
from shadowgen_contracts import (
    CreateWorkerActionRequest,
    CreateWorkerActionResponse,
    LocalRuntimeConfig,
    SystemDiagnosticsResponse,
    UpdateLocalRuntimeConfigRequest,
    UpdateLocalRuntimeConfigResponse,
)

from shadowgen_api.deps import (
    require_admin_token,
    get_runtime_config_use_case,
    get_system_diagnostics_use_case,
    get_update_runtime_config_use_case,
    get_create_worker_action_use_case,
)

router = APIRouter(prefix="/v1/system", tags=["system"])


@router.get("/diagnostics", response_model=SystemDiagnosticsResponse)
def diagnostics(
    use_case: GetSystemDiagnosticsUseCase = Depends(get_system_diagnostics_use_case),
) -> SystemDiagnosticsResponse:
    return use_case.execute()


@router.get("/runtime-config", response_model=LocalRuntimeConfig)
def get_runtime_config(
    use_case: GetRuntimeConfigUseCase = Depends(get_runtime_config_use_case),
) -> LocalRuntimeConfig:
    return use_case.execute()


@router.put("/runtime-config", response_model=UpdateLocalRuntimeConfigResponse)
def update_runtime_config(
    payload: UpdateLocalRuntimeConfigRequest,
    _admin: None = Depends(require_admin_token),
    use_case: UpdateRuntimeConfigUseCase = Depends(get_update_runtime_config_use_case),
) -> UpdateLocalRuntimeConfigResponse:
    config = use_case.execute(LocalRuntimeConfig(legacy_ml_base_url=payload.legacy_ml_base_url))
    return UpdateLocalRuntimeConfigResponse(config=config)


@router.post("/worker-actions", response_model=CreateWorkerActionResponse)
def create_worker_action(
    payload: CreateWorkerActionRequest,
    _admin: None = Depends(require_admin_token),
    use_case: CreateWorkerActionUseCase = Depends(get_create_worker_action_use_case),
) -> CreateWorkerActionResponse:
    command = use_case.execute(
        action=payload.action,
        requested_by="cloud-api",
        validation_marker="trusted:cloud-api",
    )
    return CreateWorkerActionResponse(command=command)
