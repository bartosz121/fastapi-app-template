from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from todo_api.auth.schemas import Token
    from todo_api.users.models import User


class BaseUser:
    scopes: Sequence[str]

    def __init__(self, scopes: Sequence[str] = list()) -> None:
        self.scopes = scopes

    @property
    def is_authenticated(self) -> bool:
        raise NotImplementedError()


class UnauthenticatedUser(BaseUser):
    @property
    def is_authenticated(self) -> bool:
        return False


class AuthenticatedUser(BaseUser):
    db_user: "User"
    token: "Token"

    def __init__(
        self,
        db_user: "User",
        token: "Token",
        scopes: Sequence[str] = list(),
    ) -> None:
        super().__init__(scopes)
        self.db_user = db_user
        self.token = token

    @property
    def is_authenticated(self) -> bool:
        return True
