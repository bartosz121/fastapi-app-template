from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from todo_api.todos.models import Todo


class TodoService(SQLAlchemyAsyncRepositoryService[Todo]):
    class TodoRepository(SQLAlchemyAsyncRepository[Todo]):
        model_type = Todo

    repository_type = TodoRepository
