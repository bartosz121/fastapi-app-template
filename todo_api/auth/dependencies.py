from typing import Annotated

from fastapi import Depends, Request

from todo_api.auth.service import AuthService as AuthService_
from todo_api.users.models import User


def get_auth_service() -> AuthService_:
    return AuthService_()


def get_user(request: Request) -> User:
    user = request.user
    return user


AuthService = Annotated[AuthService_, Depends(get_auth_service)]
CurrentUser = Annotated[User, Depends()]
