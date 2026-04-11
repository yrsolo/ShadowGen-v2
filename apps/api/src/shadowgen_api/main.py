from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shadowgen_api.config import ApiConfig
from shadowgen_api.routes.assets import router as assets_router
from shadowgen_api.routes.health import router as health_router
from shadowgen_api.routes.jobs import router as jobs_router
from shadowgen_api.routes.system import router as system_router


def create_app() -> FastAPI:
    config = ApiConfig()
    app = FastAPI(title=config.app_name, version="0.1.0")
    allow_origins = [item.strip() for item in config.cors_allow_origins.split(",") if item.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(assets_router)
    app.include_router(jobs_router)
    app.include_router(system_router)
    return app


app = create_app()
