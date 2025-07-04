from collections.abc import Sequence
from math import ceil
from typing import (
    Annotated,
    NamedTuple,
    TypeVar,
    cast,
)

from fastapi import Depends, Query
from pydantic import Field

from todo_api.core.exceptions import TodoApiError
from todo_api.core.schemas import BaseModel

ModelT = TypeVar("ModelT")


class PaginationError(TodoApiError): ...


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


class Paginated[ModelT](BaseModel):
    items: Sequence[ModelT]
    page: Annotated[int, Field(gt=0, description="Page number")]
    size: Annotated[int, Field(gt=0, le=100, description="Page size")]
    pages: Annotated[int, Field(gt=0, description="Number of pages")]
    total_count: Annotated[int, Field(ge=0, description="Total number of items")]

    @classmethod
    def create(
        cls,
        items: Sequence[ModelT],
        *,
        page: int,
        size: int,
        total: int | None = None,
    ) -> "Paginated[ModelT]":
        if size < 1:
            raise PaginationError("size value must be > 0")

        total_count = total or len(items)
        pages = ceil(total_count / size) if total_count > 0 else 1

        return cls.model_validate(
            {
                "items": items,
                "page": page,
                "size": size,
                "pages": pages,
                "total_count": total_count,
            }
        )
