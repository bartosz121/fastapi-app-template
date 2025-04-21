import uuid

from fastapi import FastAPI

from todo_api.core.middleware.logging import LoggingMiddleware
from todo_api.core.middleware.prometheus import PrometheusMiddleware
from todo_api.core.middleware.request_id import RequestIdMiddleware


def configure(app: FastAPI) -> None:
    app.add_middleware(
        RequestIdMiddleware,
        header_name="x-request-id",
        id_factory=lambda _: str(uuid.uuid4()),
    )
    app.add_middleware(PrometheusMiddleware)
    app.add_middleware(LoggingMiddleware)
