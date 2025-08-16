from datetime import datetime
from secrets import token_urlsafe
from typing import TYPE_CHECKING

from advanced_alchemy.base import BigIntAuditBase
from sqlalchemy import TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from todo_api.users.models import User


def generate_session_token() -> str:
    return token_urlsafe(64)


class UserSession(BigIntAuditBase):
    __tablename__ = "user_sessions"

    session_token: Mapped[str] = mapped_column(
        index=True, unique=True, default=generate_session_token
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="cascade"))
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), index=True)

    user: Mapped["User"] = relationship(innerjoin=True, lazy="joined")


__all__ = ("UserSession",)
