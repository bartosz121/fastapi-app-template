from todo_api.core.database.service import SQLAlchemyModelService
from todo_api.todos.models import Todo


class TodoService(SQLAlchemyModelService[Todo, int]):
    model = Todo
