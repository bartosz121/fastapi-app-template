from datetime import datetime, timedelta

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from fastapi.responses import Response

from todo_api.auth.models import UserSession
from todo_api.utils import utc_now


def get_session_token_from_header(auth_header: str | None) -> str | None:
    if auth_header:
        try:
            scheme, token = auth_header.split()
            if scheme.lower() == "bearer":
                return token
        except ValueError:
            pass
    return None


def create_user_session_expires_at(*, ttl: timedelta) -> datetime:
    return utc_now() + ttl


def set_auth_cookie(
    response: Response,
    cookie_name: str,
    value: str,
    *,
    expires_in: int,
    domain: str | None = None,
    secure: bool = True,
) -> None:
    response.set_cookie(
        cookie_name,  # settings.AUTH_COOKIE_NAME,
        value=value,
        expires=expires_in,
        path="/",
        domain=domain,  # settings.AUTH_COOKIE_DOMAIN,
        httponly=True,
        secure=secure,
        samesite="lax",
    )


def set_logout_cookie(
    response: Response,
    cookie_name: str,
    *,
    domain: str | None = None,
    secure: bool = True,
) -> None:
    response.set_cookie(
        cookie_name,  # settings.AUTH_COOKIE_NAME,
        value="",
        expires=0,
        path="/",
        domain=domain,  # settings.AUTH_COOKIE_DOMAIN,
        httponly=True,
        secure=secure,
        samesite="lax",
    )


class UserSessionService(SQLAlchemyAsyncRepositoryService[UserSession]):
    class UserSessionRepository(SQLAlchemyAsyncRepository[UserSession]):
        model_type = UserSession

    repository_type = UserSessionRepository
