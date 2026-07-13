from todo_api.api.schemas.base import BaseSchema, BaseSchemaId, Timestamp


class TodoBase(BaseSchema):
    title: str
    description: str | None = None
    is_completed: bool


class TodoRead(Timestamp, TodoBase, BaseSchemaId[int]): ...


class TodoCreate(TodoBase):
    is_completed: bool = False


class TodoUpdate(TodoBase): ...
