from datetime import timedelta
from enum import StrEnum

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from sqlalchemy.engine import URL


class Environment(StrEnum):
    TESTING = "TESTING"
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"

    @property
    def is_testing(self) -> bool:
        return self == Environment.TESTING

    @property
    def is_development(self) -> bool:
        return self == Environment.DEVELOPMENT

    @property
    def is_staging(self) -> bool:
        return self == Environment.STAGING

    @property
    def is_qa(self) -> bool:
        return self in {
            Environment.TESTING,
            Environment.DEVELOPMENT,
            Environment.STAGING,
        }

    @property
    def is_production(self) -> bool:
        return self == Environment.PRODUCTION


class Settings(BaseSettings):
    APP_NAME: str = "todo-api"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    LOG_LEVEL: str = "DEBUG"
    ENABLED_LOGGERS: list[str] = ["granian", "sqlalchemy", "opentelemetry"]

    OTEL_ENABLED: bool = True
    OTLP_GRPC_ENDPOINT: str = "127.0.0.1:4317"
    OTLP_EXPORTER_INSECURE: bool = True
    SECRET: SecretStr = SecretStr("Q3VmtUkDnRt17XmYdodWHC_laJ1sOFeyof7bgGP1RC4")
    USER_SESSION_TTL: int = 24 * 31  # hours
    JWT_EXPIRATION: int = 3600 * 72  # seconds
    PROMETHEUS_MULTIPROC_DIR: str | None = "/tmp/prometheus"

    DB_HOST: str = "127.0.0.1"
    DB_DATABASE: str = "todo_api"
    DB_USER: str = "todo_api"
    DB_PASSWORD: SecretStr = SecretStr("todo_api")
    DB_PORT: int = 5432

    def get_user_session_ttl_timedelta(self) -> timedelta:
        return timedelta(hours=self.USER_SESSION_TTL)

    def get_postgres_dsn(self) -> str:
        return URL.create(
            "postgresql+psycopg",
            username=self.DB_USER,
            password=self.DB_PASSWORD.get_secret_value(),
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_DATABASE,
        ).render_as_string(hide_password=False)


settings = Settings()
