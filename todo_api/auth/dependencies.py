from typing import Annotated

import structlog
from fastapi import Depends, Request

from todo_api.auth import service as auth_service
from todo_api.auth.schemas import Anonymous, Token
from todo_api.core.config import settings
from todo_api.core.database.dependencies import AsyncDbSession
from todo_api.core.exceptions import Unauthorized
from todo_api.users.models import User


async def get_user_from_jwt(
    request: Request,
    session: AsyncDbSession,
) -> User | Anonymous:
    jwt_token = request.cookies.get(
        settings.AUTH_COOKIE_NAME
    ) or auth_service.get_token_from_auth_header(request.headers.get("Authorization", None))

    if jwt_token:
        token = Token.from_str(jwt_token)
        if token and not token.is_expired():
            user = await auth_service.get_user_from_token(session, token)
            if user:
                return user

    return Anonymous()


# Extend this if scopes are needed
class Authenticator:
    allow_anonymous: bool

    def __init__(self, allow_anonymous: bool = False):
        self.allow_anonymous = allow_anonymous

    async def __call__(
        self, user: User | Anonymous = Depends(get_user_from_jwt)
    ) -> User | Anonymous:
        structlog.contextvars.bind_contextvars(user_id=user.id if isinstance(user, User) else None)
        if not self.allow_anonymous and isinstance(user, Anonymous):
            raise Unauthorized()
        return user


CurrentUserOrAnonymous = Annotated[User | Anonymous, Depends(Authenticator(allow_anonymous=True))]
CurrentUser = Annotated[User, Depends(Authenticator(allow_anonymous=False))]
