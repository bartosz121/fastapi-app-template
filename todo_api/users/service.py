from todo_api.core.service.sqlalchemy import SQLAlchemyService
from todo_api.users.models import User


class UserService(SQLAlchemyService[User, int]):
    model = User
