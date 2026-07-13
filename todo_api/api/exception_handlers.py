# pyright: reportUnusedFunction=false

import structlog
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import (
    RequestValidationError as FastApiRequestValidationError,
    ResponseValidationError as FastApiResponseValidationError,
)
from fastapi.responses import JSONResponse

from todo_api.api.exceptions import (
    ApiError,
    ConflictError,
    ErrorCode,
    ErrorResponse,
    InternalServerError,
    NotFoundError,
    ResponseValidationError,
)
from todo_api.core.database.exceptions import (
    DatabaseError,
    IntegrityConstraintError,
    RecordNotFoundError,
)
from todo_api.core.exceptions import ApplicationError

log: structlog.BoundLogger = structlog.get_logger()


def _json_response(exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response().model_dump(mode="json"),
        headers=exc.headers,
    )


def configure(app: FastAPI) -> None:
    @app.exception_handler(FastApiResponseValidationError)
    async def response_validation_error(
        request: Request, exc: FastApiResponseValidationError
    ) -> JSONResponse:
        log.error(str(exc))
        content = ResponseValidationError().model_dump(mode="json")
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=content)

    @app.exception_handler(FastApiRequestValidationError)
    async def request_validation_error(
        request: Request, exc: FastApiRequestValidationError
    ) -> JSONResponse:
        log.error(str(exc))
        content = ErrorResponse(
            error="Unprocessable Entity",
            code=ErrorCode.REQUEST_VALIDATION_ERROR,
            detail=jsonable_encoder(exc.errors()),
        ).model_dump(mode="json")
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=content)

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        log.error(exc.to_response().model_dump(mode="json"))
        return _json_response(exc)

    @app.exception_handler(RecordNotFoundError)
    async def record_not_found_error_handler(
        request: Request, exc: RecordNotFoundError
    ) -> JSONResponse:
        return _json_response(NotFoundError(detail=exc.detail, code=exc.code))

    @app.exception_handler(IntegrityConstraintError)
    async def integrity_constraint_error_handler(
        request: Request, exc: IntegrityConstraintError
    ) -> JSONResponse:
        return _json_response(ConflictError(detail=exc.detail, code=exc.code))

    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
        log.error("Database operation failed", exc_info=exc)
        return _json_response(InternalServerError())

    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        log.error("Application operation failed", exc_info=exc)
        return _json_response(InternalServerError())


__all__ = ("configure",)
