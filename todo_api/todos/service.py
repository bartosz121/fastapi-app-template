from sqlalchemy import select

from todo_api.core.service.sqlalchemy import SQLAlchemyService
from todo_api.todos.models import Todo


class TodoService(SQLAlchemyService[Todo, int]):
    model = Todo

    def list_for_user(self, user_id: int, **kwargs) -> list[Todo]:
        kwargs["statement"] = select(Todo).where(Todo.user_id == user_id)
        return self.list_(**kwargs)
