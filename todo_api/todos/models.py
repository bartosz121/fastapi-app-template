from advanced_alchemy.base import BigIntAuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class Todo(BigIntAuditBase):
    __tablename__ = "todo"

    title: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column(default=None)
    is_completed: Mapped[bool] = mapped_column(default=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


__all__ = ("Todo",)
