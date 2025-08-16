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
    from todo_api.core.database.aa_config import alchemy_async, alchemy_sync

    configure_logging()

    app = FastAPI(lifespan=lifespan)

    alchemy_async.init_app(app)
    alchemy_sync.init_app(app)

    configure_middleware(app)
    configure_exception_handlers(app)

    app.include_router(router_v1, prefix="/api")

    return app
