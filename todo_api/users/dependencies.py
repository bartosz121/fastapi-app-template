from typing import Annotated

from fastapi import Depends

from todo_api.core.database.dependencies import DbSession
from todo_api.users.service import UserService as UserService_


def get_users_service(session: DbSession) -> UserService_:
    return UserService_(session)


UserService = Annotated[UserService_, Depends(get_users_service)]
