from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI

from todo_api.core.exception_handlers import configure as configure_exception_handlers
from todo_api.core.logging import configure as configure_logging
from todo_api.core.middleware import configure as configure_middleware
from todo_api.metrics import router as metrics_router
from todo_api.todos.router import router as todos_router
from todo_api.users.router import router as users_router


class State(TypedDict): ...


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    yield {}


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(lifespan=lifespan)

    configure_middleware(app)
    configure_exception_handlers(app)

    app.include_router(metrics_router)
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(todos_router, prefix="/api/v1")

    return app
