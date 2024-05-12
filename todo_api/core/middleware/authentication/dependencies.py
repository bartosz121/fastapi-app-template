from typing import Annotated, cast

from fastapi import Depends
from fastapi.requests import Request

from todo_api.core.exceptions import Unauthorized
from todo_api.core.middleware.authentication.dto import (
    AuthenticatedUser,
    BaseUser,
)


def get_optional_user(request: Request) -> BaseUser:
    user = request.get("auth_user")
    if not isinstance(user, BaseUser):
        raise RuntimeError(
            "Unrecognized 'auth_user' in request, make sure 'AuthenticationMiddleware' is running"
        )
    return user


OptionalUser = Annotated[BaseUser, Depends(get_optional_user)]


def get_current_user(user: OptionalUser) -> AuthenticatedUser:
    if not user.is_authenticated:
        raise Unauthorized({"msg": "Unauthorized"})

    return cast(AuthenticatedUser, user)


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
