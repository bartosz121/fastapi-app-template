from todo_api.core.schemas import BaseModel, BaseModelId, Timestamp


class TodoBase(BaseModel):
    title: str
    description: str | None = None
    is_completed: bool


class TodoRead(Timestamp, TodoBase, BaseModelId[int]): ...


class TodoCreate(TodoBase): ...


class TodoUpdate(TodoBase): ...
