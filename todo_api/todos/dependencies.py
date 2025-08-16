from typing import Annotated

from fastapi import Depends

from todo_api.core.database.aa_config import alchemy_async
from todo_api.todos.service import TodoService as TodoService_

TodoService = Annotated[TodoService_, Depends(alchemy_async.provide_service(TodoService_))]
