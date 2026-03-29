from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response

from application.services.image_pipeline import ImageCompositionPipeline
from config.settings import get_settings
from domain.models import CompositionRequest

settings = get_settings()
pipeline = ImageCompositionPipeline()

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "app": settings.app_name})


@app.post("/v1/compose")
async def compose_image(file: UploadFile = File(...)) -> Response:
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    request = CompositionRequest(
        shadow_blur=settings.shadow_blur,
        shadow_opacity=settings.shadow_opacity,
        canvas_padding=settings.canvas_padding,
    )

    try:
        result = pipeline.compose(payload, request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    headers = {
        "X-Output-Width": str(result.width),
        "X-Output-Height": str(result.height),
    }
    return Response(content=result.image_bytes, media_type="image/png", headers=headers)
