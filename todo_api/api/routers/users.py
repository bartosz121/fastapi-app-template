from fastapi import APIRouter, status
from fastapi.requests import Request
from fastapi.responses import Response

from todo_api.api import auth, exceptions
from todo_api.api.dependencies.auth import (
    AnonymousUser,
    AuthCookieDomain,
    AuthCookieName,
    CurrentUser,
    CurrentUserOrAnonymous,
    UserSessionService,
)
from todo_api.api.dependencies.users import UserService
from todo_api.api.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from todo_api.api.schemas import users as schemas
from todo_api.auth import service as auth_service
from todo_api.auth.models import UserSession
from todo_api.core.config import settings
from todo_api.users import security
from todo_api.users.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=schemas.UserRead,
    responses={401: {"description": "Unauthorized", "model": exceptions.ErrorResponse}},
)
async def me(user: CurrentUser):
    return user


@router.post(
    "/login",
    response_model=schemas.LoginResponse,
    responses={
        401: {"description": "Unauthorized", "model": exceptions.ErrorResponse},
        403: {"description": "Forbidden", "model": exceptions.ErrorResponse},
    },
)
async def login(
    request: Request,
    response: Response,
    data: schemas.UserCreate,
    auth_cookie_name: AuthCookieName,
    auth_cookie_domain: AuthCookieDomain,
    user_auth: CurrentUserOrAnonymous,
    user_service: UserService,
    user_session_service: UserSessionService,
):
    if not isinstance(user_auth, AnonymousUser):
        raise ForbiddenError(code=exceptions.ErrorCode.ALREADY_LOGGED_IN)

    user = await user_service.get_one_or_none(username=data.username)
    if not user or not security.verify_password(
        data.password.get_secret_value(), user.hashed_password
    ):
        raise UnauthorizedError(
            detail="Invalid username or password",
            code=exceptions.ErrorCode.INVALID_USERNAME_OR_PASSWORD,
        )

    expires_at = auth_service.create_user_session_expires_at(
        ttl=settings.get_user_session_ttl_timedelta()
    )
    created_session = await user_session_service.create(
        UserSession(user_id=user.id, expires_at=expires_at)
    )

    auth.set_auth_cookie(
        response,
        created_session.session_token,
        auth_cookie_name=auth_cookie_name,
        auth_cookie_domain=auth_cookie_domain,
        expires_in=settings.USER_SESSION_TTL,
        secure=request.url.hostname not in ["127.0.0.1", "localhost"],
    )
    return {"token": created_session.session_token}


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserRead,
    responses={
        403: {"description": "Forbidden", "model": exceptions.ErrorResponse},
        409: {"description": "Conflict", "model": exceptions.ErrorResponse},
    },
)
async def register(
    data: schemas.UserCreate,
    user_auth: CurrentUserOrAnonymous,
    user_service: UserService,
):
    if not isinstance(user_auth, AnonymousUser):
        raise ForbiddenError(code=exceptions.ErrorCode.ALREADY_LOGGED_IN)

    if await user_service.exists(username=data.username):
        raise ConflictError(
            detail="Username already exists",
            code=exceptions.ErrorCode.USERNAME_EXISTS,
        )

    user = User(
        username=data.username,
        hashed_password=security.get_password_hash(data.password.get_secret_value()),
    )
    return await user_service.create(user)


@router.get("/logout", response_model=schemas.LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    auth_cookie_name: AuthCookieName,
    auth_cookie_domain: AuthCookieDomain,
    user_session_service: UserSessionService,
):
    if session_token := request.cookies.get(auth_cookie_name):
        if user_session := await user_session_service.get_one_or_none(session_token=session_token):
            await user_session_service.delete(user_session.id, auto_commit=True)

    auth.clear_auth_cookie(
        response,
        auth_cookie_name=auth_cookie_name,
        auth_cookie_domain=auth_cookie_domain,
        secure=request.url.hostname not in ["127.0.0.1", "localhost"],
    )
    return {"status": "ok"}
