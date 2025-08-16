from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from todo_api.users.models import User


class UserService(SQLAlchemyAsyncRepositoryService[User]):
    class UserRepository(SQLAlchemyAsyncRepository[User]):
        model_type = User

    repository_type = UserRepository
