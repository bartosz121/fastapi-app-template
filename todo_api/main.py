import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator, TypedDict

import structlog
from fastapi import FastAPI
from structlog.stdlib import BoundLogger

from todo_api.auth.service import AuthService
from todo_api.core.database.base import session_factory
from todo_api.core.exception_handlers import configure as configure_exception_handlers
from todo_api.core.logging import configure as configure_logging
from todo_api.core.middleware import logging as structlog_middleware
from todo_api.core.middleware import prometheus as prometheus_middleware
from todo_api.core.middleware import request_id as request_id_middleware
from todo_api.core.middleware.authentication import (
    AuthenticationBackend,
    AuthenticationMiddleware,
)
from todo_api.metrics import router as metrics_router
from todo_api.todos.router import router as todos_router
from todo_api.users.router import router as users_router

log: BoundLogger = structlog.get_logger()


class State(TypedDict): ...


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    yield {}


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(lifespan=lifespan)

    configure_exception_handlers(app)

    app.add_middleware(
        request_id_middleware.RequestIdMiddleware,
        header_name="x-request-id",
        id_factory=lambda _: str(uuid.uuid4()),
    )
    app.add_middleware(
        AuthenticationMiddleware,
        backend=AuthenticationBackend(AuthService(), session_factory),
    )
    app.add_middleware(prometheus_middleware.PrometheusMiddleware)
    app.add_middleware(structlog_middleware.LoggingMiddleware)
    app.add_middleware(
        request_id_middleware.RequestIdMiddleware,
        header_name="x-request-id",
        id_factory=lambda _: str(uuid.uuid4()),
    )

    app.include_router(metrics_router)
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(todos_router, prefix="/api/v1")

    return app
