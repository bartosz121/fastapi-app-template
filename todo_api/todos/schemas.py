from todo_api.core.schemas import BaseSchema, BaseSchemaId, Timestamp


class TodoBase(BaseSchema):
    title: str
    description: str | None = None
    is_completed: bool


class TodoRead(Timestamp, TodoBase, BaseSchemaId[int]): ...


class TodoCreate(TodoBase):
    is_completed: bool = False


class TodoUpdate(TodoBase): ...
