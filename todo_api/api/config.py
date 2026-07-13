from pydantic_settings import BaseSettings


class ApiSettings(BaseSettings):
    AUTH_COOKIE_NAME: str = "todo_auth"
    AUTH_COOKIE_DOMAIN: str = "127.0.0.1"
    ALLOWED_ORIGINS: list[str] = ["*"]


api_settings = ApiSettings()
