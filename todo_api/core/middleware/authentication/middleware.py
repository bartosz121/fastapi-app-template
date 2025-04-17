from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy.orm import Session
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Receive, Scope, Send
from structlog import getLogger

from todo_api.auth.schemas import Token
from todo_api.core.config import settings
from todo_api.core.middleware.authentication.dto import (
    AuthenticatedUser,
    BaseUser,
    UnauthenticatedUser,
)

if TYPE_CHECKING:
    from todo_api.auth.service import AuthService


log = getLogger()


class AuthenticationBackend:
    auth_service: "AuthService"
    session_factory: Callable[..., Session]

    def __init__(
        self, auth_service: "AuthService", session_factory: Callable[..., Session]
    ) -> None:
        self.auth_service = auth_service
        self.session_factory = session_factory

    def _get_token_from_auth_header(self, header: str | None) -> str | None:
        if header:
            try:
                scheme, token = header.split()
                if scheme.lower() == "bearer":
                    return token
            except ValueError:
                pass

        return None

    async def authenticate(self, conn: HTTPConnection) -> BaseUser:
        jwt_token = conn.cookies.get(
            settings.AUTH_COOKIE_NAME
        ) or self._get_token_from_auth_header(conn.headers.get("Authorization"))

        if jwt_token:
            token = Token.from_jwt(jwt_token)
            if token and not token.is_expired():
                with self.session_factory() as session:
                    user = self.auth_service.get_user_from_token(session, token)
                    if user:
                        return AuthenticatedUser(user, token)

        return UnauthenticatedUser()


class AuthenticationMiddleware:
    def __init__(self, app: ASGIApp, backend: AuthenticationBackend) -> None:
        self.app = app
        self.backend = backend

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> Any:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        conn = HTTPConnection(scope)

        user = await self.backend.authenticate(conn)
        scope["auth_user"] = user

        if isinstance(user, AuthenticatedUser):
            structlog.contextvars.bind_contextvars(user_id=user.db_user.id)

        await self.app(scope, receive, send)


__all__ = (
    "AuthenticationMiddleware",
    "AuthenticationBackend",
)
