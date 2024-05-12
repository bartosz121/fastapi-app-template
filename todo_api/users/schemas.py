from typing import Literal

from pydantic import SecretStr

from todo_api.core.schemas import BaseModel, BaseModelId


class UserBase(BaseModel):
    username: str


class UserRead(UserBase, BaseModelId[int]): ...


class UserCreate(BaseModel):
    username: str
    password: SecretStr


class LoginResponse(BaseModel):
    token: str


class LogoutResponse(BaseModel):
    status: Literal["ok"]
