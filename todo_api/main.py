from contextlib import asynccontextmanager
from typing import AsyncIterator, TypedDict

import structlog
from fastapi import FastAPI
from structlog.stdlib import BoundLogger

from todo_api.auth.service import AuthService
from todo_api.core import exception_handlers
from todo_api.core.config import settings
from todo_api.core.database.base import session_factory
from todo_api.core.middleware.authentication import (
    AuthenticationBackend,
    AuthenticationMiddleware,
)
from todo_api.todos.router import router as todos_router
from todo_api.users.router import router as users_router

log: BoundLogger = structlog.get_logger()


class State(TypedDict): ...


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    yield {}


def create_app() -> FastAPI:
    log.info("hello")
    app = FastAPI(lifespan=lifespan, debug=settings.ENVIRONMENT.is_qa)
    exception_handlers.configure_exception_handlers(app)

    app.add_middleware(
        AuthenticationMiddleware,
        backend=AuthenticationBackend(AuthService(), session_factory),
    )

    app.include_router(users_router, prefix="/api/v1")
    app.include_router(todos_router, prefix="/api/v1")

    return app
