from typing import Annotated, Literal, cast

from fastapi import Depends, Query

from todo_api.core.service.sqlalchemy import OrderBy


def get_timestamp_order_by_params(
    order_by: Annotated[
        str | None,
        Query(
            alias="orderBy",
            description="Order by in `^(createdAt|updatedAt)(.asc|.desc)?$` format. e.g. `createdAt.asc`",
            pattern="^(createdAt|updatedAt)(.asc|.desc)?$",
            examples=[
                "createdAt.asc",
                "createdAt.desc",
                "updatedAt.asc",
                "updatedAt.desc",
            ],
        ),
    ] = None,
) -> OrderBy | None:
    if order_by is None:
        return None

    param_field, param_order = order_by.split(".")
    param_order = cast(Literal["asc", "desc"], param_order)

    return OrderBy(
        field="created_at" if param_field == "createdAt" else "updated_at",
        order=param_order,
    )


TimestampOrderByParamsQuery = Annotated[OrderBy, Depends(get_timestamp_order_by_params)]


__all__ = ["TimestampOrderByParamsQuery"]
