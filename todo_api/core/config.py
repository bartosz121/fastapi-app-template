from enum import StrEnum

from pydantic import SecretStr, computed_field
from pydantic_core import MultiHostUrl
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
    AUTH_COOKIE_NAME: str = "todo_auth"
    AUTH_COOKIE_DOMAIN: str = "127.0.0.1"
    JWT_EXPIRATION: int = 3600 * 72  # seconds
    PROMETHEUS_MULTIPROC_DIR: str | None = None

    DB_SCHEME: str = "sqlite:///database.db"
    DB_HOST: str = ""
    DB_NAME: str = ""
    DB_USER: str = ""
    DB_PASSWORD: SecretStr | None = None
    DB_DATABASE: str = ""
    DB_PORT: int | None = None

    # computed_field type:ignore -> https://github.com/python/mypy/issues/14461

    @computed_field  # type: ignore
    @property
    def DB_URL(self) -> str:
        if self.DB_SCHEME.startswith("sqlite"):
            return self.DB_SCHEME

        return MultiHostUrl.build(
            scheme=self.DB_SCHEME,
            username=self.DB_USER,
            password=self.DB_PASSWORD.get_secret_value()
            if isinstance(self.DB_PASSWORD, SecretStr)
            else None,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_DATABASE,
        ).unicode_string()


settings = Settings()  # type: ignore
