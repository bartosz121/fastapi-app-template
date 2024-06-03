from logging import getLogger

from fastapi import FastAPI, Request, status
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse

from todo_api.core import exceptions as core_exceptions
from todo_api.core.service import exceptions as service_exceptions

log = getLogger(__name__)


def configure(app: FastAPI):
    @app.exception_handler(ResponseValidationError)
    async def response_validation_error(
        request: Request, exc: ResponseValidationError
    ) -> JSONResponse:
        log.error(str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"msg": "Internal response validation error"},
        )

    @app.exception_handler(core_exceptions.BaseError)
    async def base_error_handler(
        request: Request, exc: core_exceptions.BaseError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"msg": "Internal server error"},
        )

    @app.exception_handler(service_exceptions.NotFoundError)
    async def service_notfound_error_handler(
        request: Request, exc: service_exceptions.NotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"msg": "Not found"},
        )

    @app.exception_handler(service_exceptions.ConflictError)
    async def service_conflict_error_handler(
        request: Request, exc: service_exceptions.ConflictError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"msg": "Conflict"},
        )


__all__ = ("configure",)
