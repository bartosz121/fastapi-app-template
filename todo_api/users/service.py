from todo_api.core.database.service import SQLAlchemyModelService
from todo_api.users.models import User


class UserService(SQLAlchemyModelService[User, int]):
    model = User
