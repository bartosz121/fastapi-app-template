import logging
from enum import Enum

from fastapi import APIRouter, Response, status

from todo_api.auth.dependencies import CurrentUser
from todo_api.core import exceptions, pagination, sorting
from todo_api.todos import dependencies, schemas
from todo_api.todos.models import Todo

log = logging.getLogger(__name__)


class TodoOrderBy(str, Enum):
    created_at = "createdAt"
    updated_at = "updatedAt"


router = APIRouter(prefix="/todos", tags=["todos"])


@router.get(
    "/me",
    response_model=pagination.Paginated[schemas.TodoRead],
    responses={
        401: {
            "description": "Unauthorized",
            "model": exceptions.Unauthorized.schema(),
        }
    },
)
async def get_user_todo(
    pagination_params: pagination.PaginationParamsQuery,
    order_by: sorting.TimestampOrderByParamsQuery,
    user: CurrentUser,
    todo_service: dependencies.TodoService,
):
    todos, total = await todo_service.list_and_count(
        user_id=user.id,
        offset=pagination_params.offset,
        limit=pagination_params.limit,
        order_by=order_by,
    )

    return {
        "items": todos,
        "total": total,
        "page": pagination_params.page,
        "size": pagination_params.size,
    }


@router.get(
    "/{id}",
    response_model=schemas.TodoRead,
    responses={
        403: {
            "description": "Forbidden",
            "model": exceptions.Forbidden.schema(),
        }
    },
)
async def get_todo_by_id(
    id: int,
    user: CurrentUser,
    todo_service: dependencies.TodoService,
):
    todo = await todo_service.get_one(id=id)

    if todo.user_id != user.id:
        raise exceptions.Forbidden(code=exceptions.ErrorCode.NOT_OWNER)

    return todo


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.TodoRead,
    responses={
        401: {
            "description": "Unauthorized",
            "model": exceptions.Unauthorized.schema(),
        }
    },
)
async def create_todo(
    data: schemas.TodoCreate,
    user: CurrentUser,
    todo_service: dependencies.TodoService,
):
    todo = Todo(user_id=user.id, **data.model_dump())
    created_todo = await todo_service.create(todo)

    return created_todo


@router.put(
    "/{id}",
    response_model=schemas.TodoRead,
    responses={
        401: {
            "description": "Unauthorized",
            "model": exceptions.Unauthorized.schema(),
        },
        403: {
            "description": "Forbidden",
            "model": exceptions.Forbidden.schema(),
        },
        404: {
            "description": "Not Found",
            "model": exceptions.NotFound.schema(),
        },
    },
)
async def update_todo(
    id: int,
    user: CurrentUser,
    data: schemas.TodoUpdate,
    todo_service: dependencies.TodoService,
):
    todo_db = await todo_service.get_one(id=id)

    if todo_db.user_id != user.id:
        raise exceptions.Forbidden(code=exceptions.ErrorCode.NOT_OWNER)

    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(todo_db, k, v)

    updated_todo = await todo_service.update(todo_db)

    return updated_todo


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {
            "model": exceptions.Unauthorized.schema(),
            "description": "Unauthorized",
        },
        403: {
            "model": exceptions.Forbidden.schema(),
            "description": "Forbidden",
        },
        404: {
            "model": exceptions.NotFound.schema(),
            "description": "Not Found",
        },
    },
)
async def delete_todo(
    response: Response,
    id: int,
    user: CurrentUser,
    todo_service: dependencies.TodoService,
):
    todo = await todo_service.get_one(id=id)

    if todo.user_id != user.id:
        raise exceptions.Forbidden(code=exceptions.ErrorCode.NOT_OWNER)

    await todo_service.delete(id)

    return None
