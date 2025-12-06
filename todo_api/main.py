from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI

from todo_api.api import router_v1
from todo_api.core.exception_handlers import configure as configure_exception_handlers
from todo_api.core.logging import configure as configure_logging
from todo_api.core.middleware import configure as configure_middleware


class State(TypedDict): ...


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    yield {}


def create_app() -> FastAPI:
    from todo_api.core.config import settings
    from todo_api.core.exceptions import ResponseValidationError

    configure_logging(settings.ENABLED_LOGGERS)

    app = FastAPI(
        lifespan=lifespan,
        # Override default validation error schema
        responses={
            422: {"description": "Response Validation Error", "model": ResponseValidationError}
        },
    )

    configure_middleware(app)
    configure_exception_handlers(app)

    app.include_router(router_v1, prefix="/api")

    return app
