from typing import TypedDict

from fastapi import HTTPException as HTTPException_
from fastapi import status


class BaseError(Exception): ...


class HTTPExceptionDetail(TypedDict):
    msg: str


class HTTPException(HTTPException_, BaseError):
    def __init__(
        self,
        status_code: int,
        detail: HTTPExceptionDetail,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code, detail, headers)


class BadRequest(HTTPException):
    def __init__(
        self,
        detail: HTTPExceptionDetail,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            detail,
            headers,
        )


class Unauthorized(HTTPException):
    def __init__(
        self, detail: HTTPExceptionDetail, headers: dict[str, str] | None = None
    ) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, headers)


class Forbidden(HTTPException):
    def __init__(
        self, detail: HTTPExceptionDetail, headers: dict[str, str] | None = None
    ) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail, headers)


class NotFound(HTTPException):
    def __init__(
        self, detail: HTTPExceptionDetail, headers: dict[str, str] | None = None
    ) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail, headers)


class Conflict(HTTPException):
    def __init__(
        self, detail: HTTPExceptionDetail, headers: dict[str, str] | None = None
    ) -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail, headers)
