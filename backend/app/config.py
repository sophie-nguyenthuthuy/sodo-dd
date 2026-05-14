from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["local", "staging", "production"] = "local"
    app_name: str = "sodo-dd"
    log_level: str = "INFO"
    secret_key: str = Field(min_length=32)

    database_url: PostgresDsn
    redis_url: RedisDsn
    celery_broker_url: RedisDsn
    celery_result_backend: RedisDsn

    s3_endpoint_url: str
    s3_region: str = "ap-southeast-1"
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str
    s3_force_path_style: bool = True

    field_encryption_key: str
    field_encryption_key_id: str = "local-dev"

    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = 30
    jwt_refresh_ttl_days: int = 14
    api_key_prefix: str = "sk_"

    ocr_engine: Literal["tesseract", "vietocr", "google_vision"] = "tesseract"
    tesseract_lang: str = "vie+eng"
    ocr_dpi: int = 300

    land_portal_base_url: str = "https://dichvucong.gov.vn/p/home"
    land_portal_mode: Literal["mock", "live"] = "mock"
    land_portal_api_key: str = ""
    zoning_provider: str = "mock"
    transaction_history_provider: str = "mock"

    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 20

    sentry_dsn: str = ""
    otel_exporter_otlp_endpoint: str = ""
    prometheus_metrics_enabled: bool = True

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
