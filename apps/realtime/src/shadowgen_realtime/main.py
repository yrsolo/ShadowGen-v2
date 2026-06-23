from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shadowgen_realtime.config import RealtimeConfig
from shadowgen_realtime.events import EventBuffer, WakeBroker
from shadowgen_realtime.routes import router


def create_app() -> FastAPI:
    config = RealtimeConfig()
    app = FastAPI(title=config.app_name, version="0.1.0")
    allow_origins = [item.strip() for item in config.allowed_origins.split(",") if item.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.config = config
    app.state.event_buffer = EventBuffer(retention_sec=config.event_retention_sec)
    app.state.wake_broker = WakeBroker()
    app.include_router(router)
    return app


app = create_app()
