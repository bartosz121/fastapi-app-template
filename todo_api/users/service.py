from todo_api.core.service.sqlalchemy import SQLAlchemyModelService
from todo_api.users.models import User


class UserService(SQLAlchemyModelService[User, int]):
    model = User
