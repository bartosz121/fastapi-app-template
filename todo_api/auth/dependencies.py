from typing import Annotated
from zoneinfo import ZoneInfo

import structlog
from fastapi import Depends, Request

from todo_api.auth import service as auth_service
from todo_api.auth.service import (
    UserSessionService as UserSessionService_,
)
from todo_api.core.config import settings
from todo_api.core.database.aa_config import alchemy_async
from todo_api.core.exceptions import Unauthorized
from todo_api.users.models import User
from todo_api.utils import utc_now

UserSessionService = Annotated[
    UserSessionService_, Depends(alchemy_async.provide_service(UserSessionService_))
]


class AnonymousUser:
    pass


async def get_user_from_session(
    request: Request,
    user_session_service: UserSessionService,
) -> User | AnonymousUser:
    session_token = request.cookies.get(
        settings.AUTH_COOKIE_NAME
    ) or auth_service.get_session_token_from_header(request.headers.get("Authorization", None))

    if session_token:
        user_session = await user_session_service.get_one_or_none(session_token=session_token)
        if user_session:
            # TODO: This timezone handling is specific to SQLite
            # Remove if moving to a different database (e.g., PostgreSQL),
            expires_at_aware = user_session.expires_at
            if expires_at_aware.tzinfo is None:
                expires_at_aware = expires_at_aware.replace(tzinfo=ZoneInfo("UTC"))

            if expires_at_aware > utc_now():
                return user_session.user

    return AnonymousUser()


class Authenticator:
    allow_anonymous: bool

    def __init__(self, allow_anonymous: bool = False):
        self.allow_anonymous = allow_anonymous

    async def __call__(
        self, user: User | AnonymousUser = Depends(get_user_from_session)
    ) -> User | AnonymousUser:
        structlog.contextvars.bind_contextvars(user_id=user.id if isinstance(user, User) else None)
        if not self.allow_anonymous and isinstance(user, AnonymousUser):
            raise Unauthorized()
        return user


CurrentUserOrAnonymous = Annotated[
    User | AnonymousUser, Depends(Authenticator(allow_anonymous=True))
]
CurrentUser = Annotated[User, Depends(Authenticator(allow_anonymous=False))]
