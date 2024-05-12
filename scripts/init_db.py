# ruff: noqa: F401
from todo_api.core.config import settings
from todo_api.core.database.base import engine, metadata_
from todo_api.todos.models import Todo
from todo_api.users.models import User

if __name__ == "__main__":
    print(f"{settings.DB_URL=}")
    metadata_.create_all(engine)
