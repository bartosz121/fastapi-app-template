from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import TIMESTAMP
from sqlalchemy.engine.default import DefaultExecutionContext
from sqlalchemy.orm import Mapped, mapped_column

from todo_api.utils import utc_now


def same_as(column_name: str) -> Callable[[DefaultExecutionContext], Any]:
    """
    Returns a callable that retrieves a column value from the current execution context.

    Used as a SQLAlchemy default value function to copy the value from another column.

    Args:
        column_name: The name of the column to retrieve the value from.

    Returns:
        A callable that takes a DefaultExecutionContext and returns the column value.

    Example:
        updated_at: Mapped[datetime | None] = mapped_column(
            TIMESTAMP(timezone=True),
            default=same_as("created_at"),
        )
    """

    def inner(context: DefaultExecutionContext) -> Any:  # noqa: ANN401
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
