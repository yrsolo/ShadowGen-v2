from pydantic_settings import BaseSettings, SettingsConfigDict


class RealtimeConfig(BaseSettings):
    app_name: str = "ShadowGen Realtime"
    app_env: str = "dev"
    realtime_host: str = "0.0.0.0"
    realtime_port: int = 8082
    vps_public_base_url: str = "http://localhost:8082"
    vps_internal_token: str = "change-me-shadowgen-vps-internal"
    worker_vps_token: str = "change-me-shadowgen-worker-vps"
    vps_realtime_signing_secret: str = "change-me-shadowgen-realtime-signing"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    event_retention_sec: int = 300
    heartbeat_interval_sec: int = 15

    model_config = SettingsConfigDict(
        env_file=".env.realtime",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
