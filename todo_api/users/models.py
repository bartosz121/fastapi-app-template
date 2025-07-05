from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from todo_api.core.database.base import Model
from todo_api.core.database.mixins import TimestampMixin


class User(TimestampMixin, Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64))
    hashed_password: Mapped[str] = mapped_column(String)


__all__ = ("User",)
