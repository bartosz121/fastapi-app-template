from enum import StrEnum
from typing import ClassVar, TypedDict

from fastapi import HTTPException as HTTPException_, status


class TodoApiError(Exception): ...


class HTTPExceptionDetail(TypedDict):
    msg: str
    code: str | None


class Codes(StrEnum):
    RESPONSE_VALIDATION_ERROR = "RESPONSE_VALIDATION_ERROR"
    ALREADY_LOGGED_IN = "ALREADY_LOGGED_IN"
    INVALID_USERNAME_OR_PASSWORD = "INVALID_USERNAME_OR_PASSWORD"
    USERNAME_EXISTS = "USERNAME_EXISTS"
    NOT_OWNER = "NOT_OWNER"


class HTTPException(HTTPException_, TodoApiError):
    status_code: ClassVar[int] = status.HTTP_500_INTERNAL_SERVER_ERROR

    # FIXME: trashy, exception json should be just {"msg": "", "code": ""}, right now its wrapped in "detail"
    # its inconsistent with exception handlers
    def __init__(
        self,
        status_code: int | None = None,
        msg: str | None = None,
        code: Codes | None = None,
        detail: HTTPExceptionDetail | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            status_code or self.status_code,
            detail or {"msg": msg or self.__class__.__name__, "code": code},
            headers,
        )


class BadRequest(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST


class Unauthorized(HTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED


class Forbidden(HTTPException):
    status_code = status.HTTP_403_FORBIDDEN


class NotFound(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND


class Conflict(HTTPException):
    status_code = status.HTTP_409_CONFLICT
