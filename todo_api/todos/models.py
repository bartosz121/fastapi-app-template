from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from todo_api.core.database.base import Model
from todo_api.core.database.mixins import TimestampMixin


class Todo(TimestampMixin, Model):
    __tablename__ = "todo"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column(default=None)
    is_completed: Mapped[bool] = mapped_column(default=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
