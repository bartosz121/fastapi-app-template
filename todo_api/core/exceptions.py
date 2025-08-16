from enum import StrEnum
from typing import TypedDict

from fastapi import status
from pydantic import BaseModel, Field, create_model

from todo_api.utils import get_http_status_message


class ErrorCode(StrEnum):
    REQUEST_VALIDATION_ERROR = "REQUEST_VALIDATION_ERROR"
    RESPONSE_VALIDATION_ERROR = "RESPONSE_VALIDATION_ERROR"
    ALREADY_LOGGED_IN = "ALREADY_LOGGED_IN"
    INVALID_USERNAME_OR_PASSWORD = "INVALID_USERNAME_OR_PASSWORD"
    USERNAME_EXISTS = "USERNAME_EXISTS"
    NOT_OWNER = "NOT_OWNER"


class JSONResponseTodoApiError(TypedDict):
    error: str
    code: str | None
    detail: str | None


class TodoApiError(Exception):
    error: str
    code: ErrorCode | None
    detail: str | None
    status_code: int
    headers: dict[str, str] | None = None

    def __init__(
        self,
        *,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error: str | None = None,
        code: ErrorCode | None = None,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self.error = error or get_http_status_message(status_code)
        self.code = code
        self.detail = detail
        self.headers = headers

    def __str__(self) -> str:
        return f"{self.error}[{self.status_code}]: {self.detail}"

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(error={self.error!r}, code={self.code!r}, detail={self.detail!r}, status_code={self.status_code!r}, headers={self.headers!r})"

    def to_json_error_dict(self) -> JSONResponseTodoApiError:
        return {
            "error": self.error,
            "code": self.code,
            "detail": self.detail,
        }

    @classmethod
    def schema(cls) -> type[BaseModel]:
        """
        https://docs.pydantic.dev/latest/concepts/models/#dynamic-model-creation

        Pydantic model used in openapi responses
        """

        return create_model(
            cls.__name__,
            error=(str, Field()),
            code=(str | None, Field()),
            detail=(str | None, Field()),
        )


class BadRequest(TodoApiError):
    def __init__(
        self,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error: str | None = None,
        code: ErrorCode | None = None,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(
            error=error,
            code=code,
            detail=detail,
            status_code=status_code,
            headers=headers,
        )


class Unauthorized(TodoApiError):
    def __init__(
        self,
        *,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        code: ErrorCode | None = None,
        detail: str | None = None,
        error: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(
            error=error,
            code=code,
            detail=detail,
            status_code=status_code,
            headers=headers,
        )


class Forbidden(TodoApiError):
    def __init__(
        self,
        *,
        status_code: int = status.HTTP_403_FORBIDDEN,
        code: ErrorCode | None = None,
        detail: str | None = None,
        error: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(
            error=error,
            code=code,
            detail=detail,
            status_code=status_code,
            headers=headers,
        )


class NotFound(TodoApiError):
    def __init__(
        self,
        *,
        status_code: int = status.HTTP_404_NOT_FOUND,
        code: ErrorCode | None = None,
        detail: str | None = None,
        error: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(
            error=error,
            code=code,
            detail=detail,
            status_code=status_code,
            headers=headers,
        )


class Conflict(TodoApiError):
    def __init__(
        self,
        *,
        status_code: int = status.HTTP_409_CONFLICT,
        code: ErrorCode | None = None,
        detail: str | None = None,
        error: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(
            error=error,
            code=code,
            detail=detail,
            status_code=status_code,
            headers=headers,
        )
