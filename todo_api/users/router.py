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


@router.get("/me", response_model=schemas.UserRead)
async def me(user: CurrentUser):
    return user


@router.post("/login", response_model=schemas.LoginResponse)
async def login(
    request: Request,
    response: Response,
    data: schemas.UserCreate,
    user_auth: CurrentUserOrAnonymous,
    user_service: dependencies.UserService,
):
    if not isinstance(user_auth, Anonymous):
        raise exceptions.Forbidden(code=exceptions.Codes.ALREADY_LOGGED_IN)

    user = await user_service.get_one_or_none(username=data.username)
    if not user:
        raise exceptions.Unauthorized(
            msg="Invalid username or password",
            code=exceptions.Codes.INVALID_USERNAME_OR_PASSWORD,
        )

    if not security.verify_password(data.password.get_secret_value(), user.hashed_password):
        raise exceptions.Unauthorized(
            msg="Invalid username or password",
            code=exceptions.Codes.INVALID_USERNAME_OR_PASSWORD,
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
)
async def register(
    data: schemas.UserCreate, user_auth: CurrentUserOrAnonymous, service: dependencies.UserService
):
    if not isinstance(user_auth, Anonymous):
        raise exceptions.Forbidden(code=exceptions.Codes.ALREADY_LOGGED_IN)

    username_exists = await service.exists(username=data.username)
    if username_exists:
        raise exceptions.Conflict(
            msg="Username already exists",
            code=exceptions.Codes.USERNAME_EXISTS,
        )

    hashed_password = security.get_password_hash(data.password.get_secret_value())
    user = User(username=data.username, hashed_password=hashed_password)

    created_user = await service.create(user)

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
