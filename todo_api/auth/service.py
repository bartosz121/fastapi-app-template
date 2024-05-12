from datetime import timedelta

from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from todo_api.auth import jwt as auth_jwt
from todo_api.auth.schemas import Token
from todo_api.core.config import settings
from todo_api.users.models import User
from todo_api.utils import utc_now


class AuthService:
    @staticmethod
    def create_token(user_id: int, expires_in: timedelta | None = None) -> str:
        if expires_in is None:
            expires_in = timedelta(seconds=settings.JWT_EXPIRATION)

        expires_at = utc_now() + expires_in

        token = Token(user_id=user_id, expires_at=expires_at)

        encoded = auth_jwt.encode(
            data=token.model_dump(mode="json"),
            secret=settings.SECRET.get_secret_value(),
            expires_at=token.expires_at,
        )
        return encoded

    @staticmethod
    def get_user_from_token(session: Session, token: Token) -> User | None:
        user = session.execute(
            select(User).where(User.id == token.user_id)
        ).scalar_one_or_none()
        return user

    @staticmethod
    def set_auth_cookie(
        response: Response,
        value: str,
        *,
        expires_in: int,
        secure: bool = True,
    ) -> None:
        response.set_cookie(
            settings.AUTH_COOKIE_NAME,
            value=value,
            expires=expires_in,
            path="/",
            domain=settings.AUTH_COOKIE_DOMAIN,
            httponly=True,
            secure=secure,
            samesite="lax",
        )

    @staticmethod
    def set_logout_cookie(
        response: Response,
        *,
        secure: bool = True,
    ):
        response.set_cookie(
            settings.AUTH_COOKIE_NAME,
            value="",
            expires=0,
            path="/",
            domain=settings.AUTH_COOKIE_DOMAIN,
            httponly=True,
            secure=secure,
            samesite="lax",
        )
