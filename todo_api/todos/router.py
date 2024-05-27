from enum import Enum

from fastapi import APIRouter, Response, status

from todo_api.core import exceptions, pagination
from todo_api.core.middleware.authentication.dependencies import CurrentUser
from todo_api.todos import dependencies, schemas
from todo_api.todos.models import Todo


class TodoOrderBy(str, Enum):
    created_at = "createdAt"
    upadted_at = "upadtedAt"


router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("/me", response_model=pagination.Paginated[schemas.TodoRead])
def get_user_todo(
    pagination_params: pagination.PaginationParamsQuery,
    order_by: dependencies.TodoOrderByParamsQuery,
    user: CurrentUser,
    service: dependencies.TodoService,
):
    total_todos = service.count(user_id=user.db_user.id)
    todos = service.list_(
        user_id=user.db_user.id,
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
def get_todo_by_id(
    id: int,
    user: CurrentUser,
    service: dependencies.TodoService,
):
    todo = service.get_one(id=id)
    if todo.user_id != user.db_user.id:
        raise exceptions.Forbidden({"msg": "Forbidden"})

    return todo


@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.TodoRead)
def create_todo(
    data: schemas.TodoCreate,
    user: CurrentUser,
    service: dependencies.TodoService,
):
    todo = Todo(user_id=user.db_user.id, **data.model_dump())

    return service.create(todo)


@router.put("/{id}", response_model=schemas.TodoRead)
def update_todo(
    id: int,
    user: CurrentUser,
    data: schemas.TodoUpdate,
    service: dependencies.TodoService,
):
    todo_db = service.get_one(id=id)
    if todo_db.user_id != user.db_user.id:
        raise exceptions.Forbidden({"msg": "Forbidden"})

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(todo_db, k, v)

    return service.update(todo_db)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    response: Response,
    id: int,
    user: CurrentUser,
    service: dependencies.TodoService,
):
    todo = service.get_one(id=id)
    if todo.user_id != user.db_user.id:
        raise exceptions.Forbidden({"msg": "Forbidden"})

    service.delete(id)
    response.status_code = status.HTTP_204_NO_CONTENT

    return response
