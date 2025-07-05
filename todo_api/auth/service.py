from datetime import datetime, timedelta

from fastapi.responses import Response

from todo_api.auth.models import UserSession
from todo_api.core.config import settings
from todo_api.core.service.sqlalchemy import SQLAlchemyService
from todo_api.utils import utc_now


class UserSessionService(SQLAlchemyService[UserSession, int]):
    model = UserSession


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
    value: str,
    *,
    expires_in: int,
    secure: bool = True,
) -> None:
    response.set_cookie(
        settings.AUTH_COOKIE_NAME,
        value=value,
        expires=expires_in,
        path="/",
        domain=settings.AUTH_COOKIE_DOMAIN,
        httponly=True,
        secure=secure,
        samesite="lax",
    )


def set_logout_cookie(
    response: Response,
    *,
    secure: bool = True,
) -> None:
    response.set_cookie(
        settings.AUTH_COOKIE_NAME,
        value="",
        expires=0,
        path="/",
        domain=settings.AUTH_COOKIE_DOMAIN,
        httponly=True,
        secure=secure,
        samesite="lax",
    )
