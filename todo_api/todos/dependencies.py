from typing import Annotated, Literal, cast

from fastapi import Depends, Query

from todo_api.core.database.dependencies import DbSession
from todo_api.core.service.sqlalchemy import OrderByBase
from todo_api.todos.service import TodoService as TodoService_


def get_todo_service(session: DbSession) -> TodoService_:
    return TodoService_(session)


TodoService = Annotated[TodoService_, Depends(get_todo_service)]


class TodoOrderByParams(OrderByBase):
    field: Literal["created_at", "updated_at"]


def get_todo_order_by_params(
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
) -> TodoOrderByParams | None:
    if order_by is None:
        return None

    param_field, param_order = order_by.split(".")
    param_order = cast(Literal["asc", "desc"], param_order)

    return TodoOrderByParams(
        field="created_at" if param_field == "createdAt" else "updated_at",
        order=param_order,
    )


TodoOrderByParamsQuery = Annotated[TodoOrderByParams, Depends(get_todo_order_by_params)]
