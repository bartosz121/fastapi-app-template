from collections.abc import Sequence
from math import ceil
from typing import (
    Annotated,
    Any,
    NamedTuple,
    TypeVar,
    cast,
)

from fastapi import Depends, Query
from pydantic import Field, model_validator

from todo_api.core.exceptions import BadRequest
from todo_api.core.schemas import BaseSchema

ModelT = TypeVar("ModelT")


class PaginationError(BadRequest): ...


class PaginationParams(NamedTuple):
    page: int
    size: int

    @property
    def offset(self) -> int:
        return self.size * (self.page - 1)

    @property
    def limit(self) -> int:
        return self.size


async def get_pagination_params(
    page: int | None = Query(1, gt=0, description="Page number"),
    size: int | None = Query(50, gt=0, le=100, description="Page size"),
) -> PaginationParams:
    # Cast because of `Query` default value
    page = cast(int, page)
    size = cast(int, size)

    return PaginationParams(page, size)


PaginationParamsQuery = Annotated[PaginationParams, Depends(get_pagination_params)]


class Paginated[ModelT](BaseSchema):
    items: Sequence[ModelT]
    page: Annotated[int, Field(gt=0, description="Page number")]
    size: Annotated[int, Field(gt=0, le=100, description="Page size")]
    pages: Annotated[int | None, Field(gt=0, description="Number of pages")]
    total: Annotated[int, Field(ge=0, description="Total number of items")]

    @model_validator(mode="before")
    @classmethod
    def add_pages_if_needed(cls, data: Any) -> Any:  # noqa: ANN401
        """
        Calculate `pages` if not provided so we don't have to do this in router endpoint code
        """

        if isinstance(data, dict) and "pages" not in data:
            total = cast(Any, data.get("total"))  # pyright: ignore[reportUnknownMemberType]

            size = cast(Any, data.get("size"))  # pyright: ignore[reportUnknownMemberType]

            if isinstance(total, int) and isinstance(size, int) and size > 0:
                data["pages"] = ceil(total / size) if total > 0 and size > 0 else 1

        return data  # pyright: ignore[reportUnknownVariableType]
