from enum import StrEnum
from http import HTTPStatus
from typing import Any, ClassVar

from fastapi import status
from pydantic import BaseModel


class ErrorCode(StrEnum):
    REQUEST_VALIDATION_ERROR = "REQUEST_VALIDATION_ERROR"
    RESPONSE_VALIDATION_ERROR = "RESPONSE_VALIDATION_ERROR"
    ALREADY_LOGGED_IN = "ALREADY_LOGGED_IN"
    INVALID_USERNAME_OR_PASSWORD = "INVALID_USERNAME_OR_PASSWORD"
    USERNAME_EXISTS = "USERNAME_EXISTS"
    NOT_OWNER = "NOT_OWNER"


class ErrorResponse(BaseModel):
    error: str
    code: str | None = None
    detail: Any = None


class ResponseValidationError(ErrorResponse):
    error: str = "Response Validation Error"
    code: str | None = ErrorCode.RESPONSE_VALIDATION_ERROR
    detail: None = None


class ApiError(Exception):
    """An error whose representation is part of the HTTP API contract."""

    status_code: ClassVar[int] = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
        self,
        *,
        detail: str | None = None,
        code: str | None = None,
        error: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.error = error or HTTPStatus(self.status_code).phrase
        self.code = code
        self.detail = detail
        self.headers = headers
        super().__init__(detail)

    def to_response(self) -> ErrorResponse:
        return ErrorResponse(error=self.error, code=self.code, detail=self.detail)


class BadRequestError(ApiError):
    status_code = status.HTTP_400_BAD_REQUEST


class UnauthorizedError(ApiError):
    status_code = status.HTTP_401_UNAUTHORIZED


class ForbiddenError(ApiError):
    status_code = status.HTTP_403_FORBIDDEN


class NotFoundError(ApiError):
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(ApiError):
    status_code = status.HTTP_409_CONFLICT


class InternalServerError(ApiError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


__all__ = (
    "ApiError",
    "BadRequestError",
    "ConflictError",
    "ErrorCode",
    "ErrorResponse",
    "ForbiddenError",
    "InternalServerError",
    "NotFoundError",
    "ResponseValidationError",
    "UnauthorizedError",
)
