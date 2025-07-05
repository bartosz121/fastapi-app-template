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


@router.get("/me", response_model=pagination.Paginated[schemas.TodoRead])
async def get_user_todo(
    pagination_params: pagination.PaginationParamsQuery,
    order_by: sorting.TimestampOrderByParamsQuery,
    user: CurrentUser,
    service: dependencies.TodoService,
):
    total_todos = await service.count(user_id=user.id)
    todos = await service.list_(
        user_id=user.id,
        offset=pagination_params.offset,
        limit=pagination_params.limit,
        order_by=order_by,
    )

    return pagination.Paginated[schemas.TodoRead].create(
        [schemas.TodoRead.model_validate(todo) for todo in todos],
        size=pagination_params.size,
        page=pagination_params.page,
        total=total_todos,
    )


@router.get("/{id}", response_model=schemas.TodoRead)
async def get_todo_by_id(
    id: int,
    user: CurrentUser,
    service: dependencies.TodoService,
):
    todo = await service.get_one(id=id)

    if todo.user_id != user.id:
        raise exceptions.Forbidden(code=exceptions.Codes.NOT_OWNER)

    return todo


@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.TodoRead)
async def create_todo(
    data: schemas.TodoCreate,
    user: CurrentUser,
    service: dependencies.TodoService,
):
    todo = Todo(user_id=user.id, **data.model_dump())
    created_todo = await service.create(todo)

    return created_todo


@router.put("/{id}", response_model=schemas.TodoRead)
async def update_todo(
    id: int,
    user: CurrentUser,
    data: schemas.TodoUpdate,
    service: dependencies.TodoService,
):
    todo_db = await service.get_one(id=id)

    if todo_db.user_id != user.id:
        raise exceptions.Forbidden(code=exceptions.Codes.NOT_OWNER)

    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(todo_db, k, v)

    updated_todo = await service.update(todo_db)

    return updated_todo


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    response: Response,
    id: int,
    user: CurrentUser,
    service: dependencies.TodoService,
):
    todo = await service.get_one(id=id)

    if todo.user_id != user.id:
        raise exceptions.Forbidden(code=exceptions.Codes.NOT_OWNER)

    await service.delete(id)

    return None
