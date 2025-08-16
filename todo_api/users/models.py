from advanced_alchemy.base import BigIntAuditBase
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class User(BigIntAuditBase):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64))
    hashed_password: Mapped[str] = mapped_column(String)


__all__ = ("User",)
