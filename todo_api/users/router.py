from fastapi import APIRouter, status
from fastapi.responses import Response

from todo_api.auth.dependencies import AuthService
from todo_api.core import exceptions
from todo_api.core.config import settings
from todo_api.core.middleware.authentication.dependencies import CurrentUser
from todo_api.users import dependencies, schemas, security
from todo_api.users.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.UserRead)
def me(user: CurrentUser):
    return user.db_user


@router.post("/login", response_model=schemas.LoginResponse)
def login(
    response: Response,
    data: schemas.UserCreate,
    user_service: dependencies.UserService,
    auth_service: AuthService,
):
    user = user_service.get(username=data.username)
    if not security.verify_password(data.password.get_secret_value(), user.hashed_password):
        raise exceptions.Unauthorized(detail={"msg": "Invalid password"})

    token = auth_service.create_token(user.id)

    auth_service.set_auth_cookie(
        response,
        token,
        expires_in=settings.JWT_EXPIRATION,
        secure=settings.ENVIRONMENT.is_production,
    )

    return {"token": token}


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserRead,
)
def register(data: schemas.UserCreate, service: dependencies.UserService):
    username_exists = service.exists(username=data.username)
    if username_exists:
        raise exceptions.Conflict(detail={"msg": "Username already exists"})
    hashed_password = security.get_password_hash(data.password.get_secret_value())
    user = User(username=data.username, hashed_password=hashed_password)
    service.create(user)

    return user


@router.get("/logout", response_model=schemas.LogoutResponse)
def logout(
    response: Response,
    auth_service: AuthService,
):
    auth_service.set_logout_cookie(
        response,
        secure=settings.ENVIRONMENT.is_production,
    )
    return {"status": "ok"}
