from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerConfig(BaseSettings):
    poll_interval_sec: float = 1.0
    control_poll_interval_sec: float = 1.0
    worker_state_heartbeat_interval_sec: float = 30.0
    max_in_flight_jobs: int = 4
    submit_timeout_ms: int = 120000
    poll_interval_ms: int = 1000
    job_ttl_ms: int = 300000
    capabilities_refresh_interval_sec: float = 45.0
    max_retries: int = 3
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
    worker_control_host: str = "0.0.0.0"
    worker_control_port: int = 8081
    worker_control_token: str = "change-me-shadowgen-worker"
    worker_container_name: str = "shadowgen-worker"
    worker_image_tag: str = "shadowgen-worker-local"
    worker_workspace_mount_dest: str = "/workspace"
    worker_control_host_port: int = 8081
    worker_self_manage_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env.shadowgen",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
