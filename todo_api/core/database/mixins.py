from datetime import datetime

from sqlalchemy import TIMESTAMP
from sqlalchemy.engine.default import DefaultExecutionContext
from sqlalchemy.orm import Mapped, mapped_column

from todo_api.utils import utc_now


def same_as(column_name: str):
    def inner(context: DefaultExecutionContext):
        return context.get_current_parameters().get(column_name)

    return inner


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        index=True,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        default=same_as("created_at"),
        index=True,
        onupdate=utc_now,
    )
