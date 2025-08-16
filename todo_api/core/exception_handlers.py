# pyright: reportUnusedFunction=false

import structlog
from advanced_alchemy import exceptions as aa_exceptions
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse

from todo_api.core import exceptions as core_exceptions
from todo_api.utils import get_http_status_message

log: structlog.BoundLogger = structlog.get_logger()


def configure(app: FastAPI) -> None:
    @app.exception_handler(ResponseValidationError)
    async def response_validation_error(
        request: Request, exc: ResponseValidationError
    ) -> JSONResponse:
        log.error(str(exc))

        content: core_exceptions.JSONResponseTodoApiError = {
            "error": get_http_status_message(status.HTTP_500_INTERNAL_SERVER_ERROR),
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
            "error": get_http_status_message(status.HTTP_422_UNPROCESSABLE_ENTITY),
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

    @app.exception_handler(aa_exceptions.AdvancedAlchemyError)
    async def advanced_alchemy_error_handler(
        request: Request, exc: aa_exceptions.AdvancedAlchemyError
    ) -> JSONResponse:
        content: core_exceptions.JSONResponseTodoApiError = {
            "error": get_http_status_message(status.HTTP_500_INTERNAL_SERVER_ERROR),
            "detail": str(exc),
            "code": None,
        }
        log.error(f"AdvancedAlchemyError handler: {exc=!s}; {content=}")

        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)

    @app.exception_handler(aa_exceptions.NotFoundError)
    async def aa_not_found_error_handler(
        request: Request, exc: aa_exceptions.NotFoundError
    ) -> JSONResponse:
        content: core_exceptions.JSONResponseTodoApiError = {
            "error": get_http_status_message(status.HTTP_404_NOT_FOUND),
            "detail": str(exc),
            "code": None,
        }
        log.error(f"{exc=!s}; {content=}")

        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=content)

    @app.exception_handler(aa_exceptions.MultipleResultsFoundError)
    async def aa_multiple_results_found_error_handler(
        request: Request, exc: aa_exceptions.MultipleResultsFoundError
    ) -> JSONResponse:
        content: core_exceptions.JSONResponseTodoApiError = {
            "error": get_http_status_message(status.HTTP_409_CONFLICT),
            "detail": str(exc),
            "code": None,
        }
        log.error(f"{exc=!s}; {content=}")

        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=content)

    @app.exception_handler(aa_exceptions.IntegrityError)
    async def aa_integrity_error_handler(
        request: Request, exc: aa_exceptions.IntegrityError
    ) -> JSONResponse:
        content: core_exceptions.JSONResponseTodoApiError = {
            "error": get_http_status_message(status.HTTP_409_CONFLICT),
            "detail": str(exc),
            "code": None,
        }
        log.error(f"{exc=!s}; {content=}")

        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=content)


__all__ = ("configure",)
