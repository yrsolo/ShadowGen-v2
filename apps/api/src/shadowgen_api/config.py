from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiConfig(BaseSettings):
    app_name: str = "ShadowGen API"
    app_env: str = "dev"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    state_backend: str = "file"
    state_dir: str = ".shadowgen-local"
    s3_endpoint_url: str | None = Field(default=None, validation_alias=AliasChoices("S3_ENDPOINT_URL"))
    s3_bucket: str | None = Field(default=None, validation_alias=AliasChoices("S3_BUCKET"))
    s3_region: str = "ru-central1"
    s3_access_key_id: str | None = Field(default=None, validation_alias=AliasChoices("S3_ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID"))
    s3_secret_access_key: str | None = Field(default=None, validation_alias=AliasChoices("S3_SECRET_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY"))
    s3_prefix: str = "shadowgen-v2"
    queue_backend: str = "file"
    queue_poll_wait_sec: int = 2
    ymq_endpoint: str | None = None
    ymq_queue_url: str | None = None
    ymq_region: str = "ru-central1"
    ymq_access_key_id: str | None = Field(default=None, validation_alias=AliasChoices("YMQ_ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID"))
    ymq_secret_access_key: str | None = Field(default=None, validation_alias=AliasChoices("YMQ_SECRET_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY"))
    legacy_ml_base_url: str | None = None
    legacy_ml_timeout_sec: float = 120.0

    model_config = SettingsConfigDict(
        env_file=".env.shadowgen",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
