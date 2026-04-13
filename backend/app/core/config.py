from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="CodeGuard", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_cors_origins: list[str] | str = Field(default="http://localhost:8080", alias="APP_CORS_ORIGINS")
    ai_provider_order: list[str] | str = Field(default="modal,groq", alias="AI_PROVIDER_ORDER")
    ai_provider_concurrency_limit: int = Field(default=2, alias="AI_PROVIDER_CONCURRENCY_LIMIT")
    ai_provider_cooldown_seconds: float = Field(default=8.0, alias="AI_PROVIDER_COOLDOWN_SECONDS")
    ai_provider_failure_threshold: int = Field(default=2, alias="AI_PROVIDER_FAILURE_THRESHOLD")
    ai_provider_quarantine_seconds: float = Field(default=30.0, alias="AI_PROVIDER_QUARANTINE_SECONDS")
    ai_response_cache_ttl_seconds: int = Field(default=900, alias="AI_RESPONSE_CACHE_TTL_SECONDS")

    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_api_keys: list[str] | str | None = Field(default=None, alias="GROQ_API_KEYS")
    groq_base_url: str = Field(default="https://api.groq.com", alias="GROQ_BASE_URL")
    groq_model: str = Field(default="openai/gpt-oss-120b", alias="GROQ_MODEL")
    groq_small_model: str = Field(default="openai/gpt-oss-20b", alias="GROQ_SMALL_MODEL")
    groq_large_model: str = Field(default="openai/gpt-oss-120b", alias="GROQ_LARGE_MODEL")
    groq_overflow_model: str = Field(default="groq/compound-mini", alias="GROQ_OVERFLOW_MODEL")
    groq_secondary_fallback_model: str | None = Field(default="meta-llama/llama-4-scout-17b-16e-instruct", alias="GROQ_SECONDARY_FALLBACK_MODEL")
    groq_key_cooldown_seconds: float = Field(default=8.0, alias="GROQ_KEY_COOLDOWN_SECONDS")
    groq_key_failure_threshold: int = Field(default=2, alias="GROQ_KEY_FAILURE_THRESHOLD")
    groq_key_quarantine_seconds: float = Field(default=45.0, alias="GROQ_KEY_QUARANTINE_SECONDS")
    groq_requests_per_minute: int = Field(default=1000, alias="GROQ_REQUESTS_PER_MINUTE")
    groq_tokens_per_minute: int = Field(default=250000, alias="GROQ_TOKENS_PER_MINUTE")
    groq_requests_per_day: int = Field(default=500000, alias="GROQ_REQUESTS_PER_DAY")

    modal_api_key: str | None = Field(default=None, alias="MODAL_API_KEY")
    modal_base_url: str = Field(default="https://api.us-west-2.modal.direct/v1", alias="MODAL_BASE_URL")
    modal_model: str = Field(default="zai-org/GLM-5-FP8", alias="MODAL_MODEL")
    modal_small_model: str | None = Field(default=None, alias="MODAL_SMALL_MODEL")
    modal_large_model: str | None = Field(default=None, alias="MODAL_LARGE_MODEL")

    nvidia_api_key: str | None = Field(default=None, alias="NVIDIA_API_KEY")
    nvidia_base_url: str = Field(default="https://integrate.api.nvidia.com/v1", alias="NVIDIA_BASE_URL")
    nvidia_model: str = Field(default="openai/gpt-oss-120b", alias="NVIDIA_MODEL")
    nvidia_small_model: str | None = Field(default=None, alias="NVIDIA_SMALL_MODEL")
    nvidia_large_model: str | None = Field(default=None, alias="NVIDIA_LARGE_MODEL")
    nvidia_overflow_model: str | None = Field(default=None, alias="NVIDIA_OVERFLOW_MODEL")
    nvidia_enable_thinking: bool = Field(default=True, alias="NVIDIA_ENABLE_THINKING")

    mongodb_uri: str = Field(alias="MONGODB_URI")
    mongodb_database: str = Field(default="CodeGuard", alias="MONGODB_DATABASE")

    @field_validator("app_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: list[str] | str):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("ai_provider_order", mode="before")
    @classmethod
    def parse_provider_order(cls, value: list[str] | str):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("groq_api_keys", mode="before")
    @classmethod
    def parse_groq_api_keys(cls, value: list[str] | str | None):
        if value is None:
            return None
        if isinstance(value, str):
            raw = value.replace("\n", ",")
            return [item.strip() for item in raw.split(",") if item.strip()]
        return value

    @field_validator("groq_base_url", mode="before")
    @classmethod
    def normalize_groq_base_url(cls, value: str):
        normalized = str(value).strip().rstrip("/")
        if normalized.endswith("/openai/v1"):
            return normalized[: -len("/openai/v1")]
        return normalized


@lru_cache
def get_settings() -> Settings:
    return Settings()
