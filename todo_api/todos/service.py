from todo_api.core.service.sqlalchemy import SQLAlchemyModelService
from todo_api.todos.models import Todo


class TodoService(SQLAlchemyModelService[Todo, int]):
    model = Todo
