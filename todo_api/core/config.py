from datetime import timedelta
from enum import StrEnum
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings


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
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    LOG_LEVEL: str = "DEBUG"

    SECRET: SecretStr = SecretStr("Q3VmtUkDnRt17XmYdodWHC_laJ1sOFeyof7bgGP1RC4")
    USER_SESSION_TTL: int = 24 * 31  # hours
    AUTH_COOKIE_NAME: str = "todo_auth"
    AUTH_COOKIE_DOMAIN: str = "127.0.0.1"
    JWT_EXPIRATION: int = 3600 * 72  # seconds
    PROMETHEUS_MULTIPROC_DIR: str | None = None

    DB_SCHEME: str = "sqlite:///database.db"
    # postgres
    # DB_HOST: str = ""
    # DB_NAME: str = ""
    # DB_USER: str = ""
    # DB_PASSWORD: SecretStr
    # DB_DATABASE: str = ""
    # DB_PORT: int

    def get_sqlite_dsn(self, *, driver: Literal["aiosqlite"] | None = None) -> str:
        if driver is None:
            return self.DB_SCHEME
        return f"sqlite+{driver}:///database.db"

    def get_user_session_ttl_timedelta(self) -> timedelta:
        return timedelta(hours=self.USER_SESSION_TTL)

    # postgres
    # def get_postgres_dsn(self, driver: Literal["asyncpg", "psycopg2"]) -> str:
    #     return str(
    #         PostgresDsn.build(
    #             scheme=f"postgresql+{driver}",
    #             username=self.DB_USER,
    #             password=self.DB_PASSWORD.get_secret_value(),
    #             host=self.DB_HOST,
    #             port=self.DB_PORT,
    #             path=self.DB_DATABASE,
    #         )
    #     )


settings = Settings()
