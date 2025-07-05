from datetime import datetime
from typing import Self

import jwt
from pydantic import (
    ValidationError,
    field_serializer,
)
from structlog import getLogger

from todo_api.auth import jwt as auth_jwt
from todo_api.core.config import settings
from todo_api.core.schemas import BaseModel
from todo_api.utils import utc_now

log = getLogger(__name__)


class Anonymous: ...


class Token(BaseModel):
    user_id: int
    expires_at: datetime

    def is_expired(self) -> bool:
        return self.expires_at < utc_now()

    @field_serializer("expires_at")
    def serialize_expires_at(self, dt: datetime) -> int:
        return int(dt.timestamp())

    @classmethod
    def from_str(cls, token_str: str) -> Self | None:
        try:
            decoded = auth_jwt.decode(token=token_str, secret=settings.SECRET.get_secret_value())
            token = cls.model_validate(decoded)
        except (
            KeyError,
            jwt.DecodeError,
            jwt.ExpiredSignatureError,
            ValidationError,
        ) as exc:
            log.warning("Token.from_jwt exception: %s", str(exc))
            return None
        else:
            return token
