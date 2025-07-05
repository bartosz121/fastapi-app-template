from fastapi import APIRouter, status
from fastapi.requests import Request
from fastapi.responses import Response

from todo_api.auth import service as auth_service
from todo_api.auth.dependencies import CurrentUser, CurrentUserOrAnonymous
from todo_api.auth.schemas import Anonymous
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
):
    if not isinstance(user_auth, Anonymous):
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

    token = auth_service.create_token(user.id)

    is_localhost = request.url.hostname in ["127.0.0.1", "localhost"]
    secure = False if is_localhost else True
    auth_service.set_auth_cookie(
        response,
        token,
        expires_in=settings.JWT_EXPIRATION,
        secure=secure,
    )

    return {"token": token}


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
    if not isinstance(user_auth, Anonymous):
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
):
    is_localhost = request.url.hostname in ["127.0.0.1", "localhost"]
    secure = False if is_localhost else True
    auth_service.set_logout_cookie(
        response,
        secure=secure,
    )

    return {"status": "ok"}
