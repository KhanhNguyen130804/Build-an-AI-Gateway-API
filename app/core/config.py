from typing import Annotated, Literal

from pydantic import Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_core import PydanticCustomError
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

PositiveInt = Annotated[int, Field(gt=0)]


class ConfigurationError(Exception):
    """Safe error with field names only: never include Pydantic input values."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    port: int = Field(default=8000, ge=1, le=65535)
    database_url: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    openai_model: str | None = None
    jwt_secret: SecretStr | None = None
    rate_limit_hash_secret: SecretStr | None = None
    jwt_issuer: str = "ai-gateway"
    jwt_audience: str = "ai-gateway-clients"
    jwt_ttl_seconds: PositiveInt = 3600
    ai_requests_per_minute: PositiveInt = 10
    ai_requests_per_user_day: PositiveInt = 100
    ai_requests_per_gateway_day: PositiveInt = 300
    auth_requests_per_ip_minute: PositiveInt = 5
    request_deadline_seconds: float = Field(default=30, ge=5)
    llm_deadline_seconds: float = Field(default=27, gt=0)
    attempt_timeout_seconds: float = Field(default=10, gt=0)
    connect_timeout_seconds: float = Field(default=3, gt=0)
    database_check_timeout_seconds: float = Field(default=2, gt=0, le=10)
    max_provider_attempts: int = Field(default=3, ge=1, le=3)
    sdk_max_retries: int = Field(default=0, ge=0, le=0)
    chat_max_output_tokens: PositiveInt = 512
    analyze_max_output_tokens: PositiveInt = 1024
    max_context_messages: PositiveInt = 20
    max_context_characters: PositiveInt = 40000
    max_body_bytes: int = Field(default=65536, ge=1024, le=1048576)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    allowed_origins: str = ""
    demo_username: str = "reviewer"
    demo_password: SecretStr | None = None
    second_test_username: str = "other-reviewer"
    second_test_password: SecretStr | None = None

    @field_validator(
        "database_url",
        "openai_api_key",
        "openai_model",
        "jwt_secret",
        "rate_limit_hash_secret",
        "demo_password",
        "second_test_password",
        mode="before",
    )
    @classmethod
    def empty_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("jwt_secret", "rate_limit_hash_secret")
    @classmethod
    def strong_secret(cls, value: SecretStr | None):
        if value and len(value.get_secret_value()) < 32:
            raise ValueError("Secret must have at least 32 characters")
        return value

    @field_validator("database_url")
    @classmethod
    def postgres_only(cls, value: SecretStr | None):
        if value:
            try:
                url = make_url(value.get_secret_value())
            except Exception:
                raise ValueError("Invalid PostgreSQL URL") from None
            if url.drivername not in {"postgres", "postgresql", "postgresql+psycopg"}:
                raise ValueError("Only PostgreSQL with the psycopg driver is supported")
        return value

    @model_validator(mode="after")
    def validate_budgets(self):
        if self.llm_deadline_seconds > self.request_deadline_seconds - 3:
            raise ValueError("LLM deadline must reserve at least 3 seconds for finalization")
        if self.attempt_timeout_seconds > self.llm_deadline_seconds:
            raise ValueError("Attempt timeout exceeds the LLM deadline")
        if self.connect_timeout_seconds > self.attempt_timeout_seconds:
            raise ValueError("Connect timeout exceeds the attempt timeout")
        if self.app_env == "production":
            missing = [
                name
                for name in (
                    "database_url",
                    "openai_api_key",
                    "openai_model",
                    "jwt_secret",
                    "rate_limit_hash_secret",
                )
                if not getattr(self, name)
            ]
            if missing:
                raise PydanticCustomError(
                    "missing_production_configuration",
                    "Missing production configuration: {fields}",
                    {"fields": ", ".join(missing)},
                )
        return self

    def redaction_values(self) -> tuple[str, ...]:
        return tuple(
            value.get_secret_value()
            for name in type(self).model_fields
            if isinstance(value := getattr(self, name), SecretStr)
        )


def load_settings(**overrides) -> Settings:
    try:
        return Settings(**overrides)
    except ValidationError as exc:
        fields = set(
            {".".join(map(str, error["loc"])) or "configuration" for error in exc.errors()}
        )
        for error in exc.errors():
            if error["type"] == "missing_production_configuration":
                fields.update(error["ctx"]["fields"].split(", "))
        raise ConfigurationError(
            "Invalid configuration fields: " + ", ".join(sorted(fields))
        ) from None
