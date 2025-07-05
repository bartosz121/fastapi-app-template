# pyright: reportUnusedFunction=false

import structlog
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse

from todo_api.core import exceptions as core_exceptions

log: structlog.BoundLogger = structlog.get_logger()


def configure(app: FastAPI) -> None:
    @app.exception_handler(ResponseValidationError)
    async def response_validation_error(
        request: Request, exc: ResponseValidationError
    ) -> JSONResponse:
        log.error(str(exc))

        content: core_exceptions.JSONResponseTodoApiError = {
            "error": "Internal Server Error",
            "code": core_exceptions.ErrorCode.RESPONSE_VALIDATION_ERROR,
            "detail": None,
        }

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=content,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        log.error(str(exc))
        content: core_exceptions.JSONResponseTodoApiError = {
            "error": "Unprocessable Entity",
            "code": core_exceptions.ErrorCode.REQUEST_VALIDATION_ERROR,
            "detail": jsonable_encoder(exc.errors()),
        }

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=content,
        )

    @app.exception_handler(core_exceptions.TodoApiError)
    async def todo_api_error_error_handler(
        request: Request, exc: core_exceptions.TodoApiError
    ) -> JSONResponse:
        content: core_exceptions.JSONResponseTodoApiError = exc.to_json_error_dict()
        log.error(content)

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=exc.headers,
        )


__all__ = ("configure",)
