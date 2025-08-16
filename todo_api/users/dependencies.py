from typing import Annotated

from fastapi import Depends

from todo_api.core.database.aa_config import alchemy_async
from todo_api.users.service import UserService as UserService_

UserService = Annotated[UserService_, Depends(alchemy_async.provide_service(UserService_))]
