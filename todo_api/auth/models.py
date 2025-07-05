from datetime import datetime
from secrets import token_urlsafe

from sqlalchemy import TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from todo_api.core.database.base import Model
from todo_api.core.database.mixins import TimestampMixin
from todo_api.users.models import User


def generate_session_token() -> str:
    return token_urlsafe(64)


class UserSession(Model, TimestampMixin):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_token: Mapped[str] = mapped_column(
        index=True, unique=True, default=generate_session_token
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="cascade"))
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), index=True)

    user: Mapped["User"] = relationship(lazy="joined")


__all__ = ("UserSession",)
