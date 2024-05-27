from todo_api.core.service.sqlalchemy import SQLAlchemyService
from todo_api.todos.models import Todo


class TodoService(SQLAlchemyService[Todo, int]):
    model = Todo
