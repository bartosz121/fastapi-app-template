from fastapi import APIRouter, status
from fastapi.requests import Request
from fastapi.responses import Response

from todo_api.auth import service as auth_service
from todo_api.auth.dependencies import (
    AnonymousUser,
    CurrentUser,
    CurrentUserOrAnonymous,
    UserSessionService,
)
from todo_api.auth.models import UserSession
from todo_api.core import exceptions
from todo_api.core.config import settings
from todo_api.users import dependencies, schemas, security
from todo_api.users.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=schemas.UserRead,
    responses={
        401: {
            "description": "Unauthorized",
            "model": exceptions.Unauthorized.schema(),
        }
    },
)
async def me(user: CurrentUser):
    return user


@router.post(
    "/login",
    response_model=schemas.LoginResponse,
    responses={
        403: {
            "description": "Forbidden",
            "model": exceptions.Forbidden.schema(),
        },
        401: {
            "description": "Unauthorized",
            "model": exceptions.Unauthorized.schema(),
        },
    },
)
async def login(
    request: Request,
    response: Response,
    data: schemas.UserCreate,
    user_auth: CurrentUserOrAnonymous,
    user_service: dependencies.UserService,
    user_session_service: UserSessionService,
):
    if not isinstance(user_auth, AnonymousUser):
        raise exceptions.Forbidden(code=exceptions.ErrorCode.ALREADY_LOGGED_IN)

    user = await user_service.get_one_or_none(username=data.username)
    if not user:
        raise exceptions.Unauthorized(
            detail="Invalid username or password",
            code=exceptions.ErrorCode.INVALID_USERNAME_OR_PASSWORD,
        )

    if not security.verify_password(data.password.get_secret_value(), user.hashed_password):
        raise exceptions.Unauthorized(
            detail="Invalid username or password",
            code=exceptions.ErrorCode.INVALID_USERNAME_OR_PASSWORD,
        )

    expires_at = auth_service.create_user_session_expires_at(
        ttl=settings.get_user_session_ttl_timedelta()
    )
    user_session = UserSession(user_id=user.id, expires_at=expires_at)
    created_session = await user_session_service.create(user_session)

    is_localhost = request.url.hostname in ["127.0.0.1", "localhost"]
    secure = not is_localhost
    auth_service.set_auth_cookie(
        response,
        settings.AUTH_COOKIE_NAME,
        created_session.session_token,
        expires_in=settings.USER_SESSION_TTL,
        domain=settings.AUTH_COOKIE_DOMAIN,
        secure=secure,
    )

    return {"token": created_session.session_token}


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserRead,
    responses={
        403: {
            "description": "Forbidden",
            "model": exceptions.Forbidden.schema(),
        },
        409: {
            "description": "Conflict",
            "model": exceptions.Conflict.schema(),
        },
    },
)
async def register(
    data: schemas.UserCreate,
    user_auth: CurrentUserOrAnonymous,
    user_service: dependencies.UserService,
):
    if not isinstance(user_auth, AnonymousUser):
        raise exceptions.Forbidden(code=exceptions.ErrorCode.ALREADY_LOGGED_IN)

    username_exists = await user_service.exists(username=data.username)
    if username_exists:
        raise exceptions.Conflict(
            detail="Username already exists",
            code=exceptions.ErrorCode.USERNAME_EXISTS,
        )

    hashed_password = security.get_password_hash(data.password.get_secret_value())
    user = User(username=data.username, hashed_password=hashed_password)

    created_user = await user_service.create(user)

    return created_user


@router.get("/logout", response_model=schemas.LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    user_session_service: UserSessionService,
):
    session_token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    if session_token:
        user_session = await user_session_service.get_one_or_none(session_token=session_token)
        if user_session:
            await user_session_service.delete(user_session.id, auto_commit=True)

    is_localhost = request.url.hostname in ["127.0.0.1", "localhost"]
    secure = not is_localhost
    auth_service.set_logout_cookie(
        response,
        settings.AUTH_COOKIE_NAME,
        domain=settings.AUTH_COOKIE_DOMAIN,
        secure=secure,
    )

    return {"status": "ok"}
