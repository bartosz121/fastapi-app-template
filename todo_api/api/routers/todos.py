from fastapi import APIRouter, status

from todo_api.api import exceptions, pagination, sorting
from todo_api.api.dependencies.auth import CurrentUser
from todo_api.api.dependencies.todos import TodoService
from todo_api.api.exceptions import ForbiddenError
from todo_api.api.schemas import todos as schemas
from todo_api.todos.models import Todo

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get(
    "/me",
    response_model=pagination.Paginated[schemas.TodoRead],
    responses={401: {"description": "Unauthorized", "model": exceptions.ErrorResponse}},
)
async def get_user_todo(
    pagination_params: pagination.PaginationParamsQuery,
    order_by: sorting.TimestampOrderByParamsQuery,
    user: CurrentUser,
    todo_service: TodoService,
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
    responses={403: {"description": "Forbidden", "model": exceptions.ErrorResponse}},
)
async def get_todo_by_id(id: int, user: CurrentUser, todo_service: TodoService):
    todo = await todo_service.get_one(id=id)
    if todo.user_id != user.id:
        raise ForbiddenError(code=exceptions.ErrorCode.NOT_OWNER)
    return todo


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.TodoRead,
    responses={401: {"description": "Unauthorized", "model": exceptions.ErrorResponse}},
)
async def create_todo(data: schemas.TodoCreate, user: CurrentUser, todo_service: TodoService):
    return await todo_service.create(Todo(user_id=user.id, **data.model_dump()))


@router.put(
    "/{id}",
    response_model=schemas.TodoRead,
    responses={
        401: {"description": "Unauthorized", "model": exceptions.ErrorResponse},
        403: {"description": "Forbidden", "model": exceptions.ErrorResponse},
        404: {"description": "Not Found", "model": exceptions.ErrorResponse},
    },
)
async def update_todo(
    id: int,
    user: CurrentUser,
    data: schemas.TodoUpdate,
    todo_service: TodoService,
):
    todo = await todo_service.get_one(id=id)
    if todo.user_id != user.id:
        raise ForbiddenError(code=exceptions.ErrorCode.NOT_OWNER)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(todo, key, value)
    return await todo_service.update(todo)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Unauthorized", "model": exceptions.ErrorResponse},
        403: {"description": "Forbidden", "model": exceptions.ErrorResponse},
        404: {"description": "Not Found", "model": exceptions.ErrorResponse},
    },
)
async def delete_todo(id: int, user: CurrentUser, todo_service: TodoService):
    todo = await todo_service.get_one(id=id)
    if todo.user_id != user.id:
        raise ForbiddenError(code=exceptions.ErrorCode.NOT_OWNER)
    await todo_service.delete(id)
