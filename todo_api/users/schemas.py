from typing import Literal

from pydantic import SecretStr

from todo_api.core.schemas import BaseSchema, BaseSchemaId


class UserBase(BaseSchema):
    username: str


class UserRead(UserBase, BaseSchemaId[int]): ...


class UserCreate(BaseSchema):
    username: str
    password: SecretStr


class LoginResponse(BaseSchema):
    token: str


class LogoutResponse(BaseSchema):
    status: Literal["ok"]
