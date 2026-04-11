from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse, Response

from shadowgen_application.ports import AssetStorePort
from shadowgen_application.use_cases.upload_asset import UploadAssetUseCase
from shadowgen_contracts import CreateAssetResponse, GetAssetResponse

from shadowgen_api.deps import get_asset_store, get_upload_asset_use_case

router = APIRouter(prefix="/v1/assets", tags=["assets"])


@router.post("", response_model=CreateAssetResponse)
async def upload_asset(
    file: UploadFile = File(...),
    use_case: UploadAssetUseCase = Depends(get_upload_asset_use_case),
):
    payload = await file.read()
    asset_ref = use_case.execute(payload, file.content_type or "application/octet-stream")
    return CreateAssetResponse(asset=asset_ref)


@router.get("/{asset_id}", response_model=GetAssetResponse)
def get_asset(asset_id: str, asset_store: AssetStorePort = Depends(get_asset_store)):
    asset_ref = asset_store.get_ref(asset_id)
    if asset_ref is None:
        return JSONResponse({"error": {"code": "asset_not_found", "message": "Asset not found"}}, status_code=404)
    return GetAssetResponse(asset=asset_ref)


@router.get("/{asset_id}/content")
def get_asset_content(asset_id: str, asset_store: AssetStorePort = Depends(get_asset_store)):
    asset_ref = asset_store.get_ref(asset_id)
    if asset_ref is None:
        return JSONResponse({"error": {"code": "asset_not_found", "message": "Asset not found"}}, status_code=404)
    payload = asset_store.get_bytes(asset_id)
    return Response(content=payload, media_type=asset_ref.mime_type, headers={"Content-Disposition": "inline"})
