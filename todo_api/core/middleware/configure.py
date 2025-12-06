import uuid
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI

from todo_api.core.middleware.logging import LoggingMiddleware
from todo_api.core.middleware.prometheus import PrometheusMiddleware
from todo_api.core.middleware.request_id import RequestIdMiddleware

if TYPE_CHECKING:
    from todo_api.core.config import Environment

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


def configure(app: FastAPI, environment: Environment) -> None:
    app.add_middleware(
        RequestIdMiddleware,
        header_name="x-request-id",
        id_factory=lambda _: str(uuid.uuid4()),
    )

    if not environment.is_testing:
        logger.info("Prometheus middleware enabled")
        app.add_middleware(PrometheusMiddleware)

    app.add_middleware(LoggingMiddleware)
