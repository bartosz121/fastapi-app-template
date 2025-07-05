from enum import StrEnum
from typing import TypedDict

from fastapi import status
from pydantic import BaseModel, Field, create_model


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
        error: str = "Internal Server Error",
        code: ErrorCode | None = None,
        detail: str | None = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers: dict[str, str] | None = None,
    ):
        self.error = error
        self.code = code
        self.detail = detail
        self.status_code = status_code
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
        error: str = "Bad Request",
        code: ErrorCode | None = None,
        detail: str | None = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
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
        error: str = "Unauthorized",
        code: ErrorCode | None = None,
        detail: str | None = None,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
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
        error: str = "Forbidden",
        code: ErrorCode | None = None,
        detail: str | None = None,
        status_code: int = status.HTTP_403_FORBIDDEN,
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
        error: str = "Not Found",
        code: ErrorCode | None = None,
        detail: str | None = None,
        status_code: int = status.HTTP_404_NOT_FOUND,
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
        error: str = "Conflict",
        code: ErrorCode | None = None,
        detail: str | None = None,
        status_code: int = status.HTTP_409_CONFLICT,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(
            error=error,
            code=code,
            detail=detail,
            status_code=status_code,
            headers=headers,
        )
