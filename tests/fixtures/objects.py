from tests.fixtures.database import SaveModel
from todo_api.todos.models import Todo
from todo_api.users.models import User
from todo_api.users.security import get_password_hash


async def create_user(
    save_model_fixture: SaveModel, *, username: str = "user1", password: str = "password123"
) -> User:
    user = User(username=username, hashed_password=get_password_hash(password))
    await save_model_fixture(user)
    return user


async def create_todo(
    save_model_fixture: SaveModel,
    *,
    user_id: int,
    title: str = "Title",
    description: str | None = "Description",
    is_completed: bool = False,
) -> Todo:
    todo = Todo(title=title, description=description, is_completed=is_completed, user_id=user_id)
    await save_model_fixture(todo)
    return todo
