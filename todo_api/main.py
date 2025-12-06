from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI

from todo_api.api import router_v1
from todo_api.core.exception_handlers import configure as configure_exception_handlers
from todo_api.core.logging import configure as configure_logging
from todo_api.core.middleware import configure as configure_middleware


class State(TypedDict):
    auth_cookie_name: str
    auth_cookie_domain: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    from todo_api.core.config import settings

    yield {
        "auth_cookie_name": settings.AUTH_COOKIE_NAME,
        "auth_cookie_domain": settings.AUTH_COOKIE_DOMAIN,
    }


def create_app() -> FastAPI:
    from todo_api.core.config import settings
    from todo_api.core.exceptions import ResponseValidationError
    from todo_api.version import __version__

    configure_logging(settings.LOG_LEVEL, settings.ENVIRONMENT, settings.ENABLED_LOGGERS)

    app = FastAPI(
        version=__version__,
        lifespan=lifespan,
        # Override default validation error schema
        responses={
            422: {"description": "Response Validation Error", "model": ResponseValidationError}
        },
    )

    configure_middleware(app, settings.ENVIRONMENT)
    configure_exception_handlers(app)

    app.include_router(router_v1, prefix="/api")

    return app
