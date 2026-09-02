import uuid
from typing import TypedDict, Unpack, cast

import structlog
from fastapi import FastAPI
from starlette.types import ASGIApp

from todo_api.api.middleware.logging import LoggingMiddleware
from todo_api.api.middleware.prometheus import PrometheusMiddleware
from todo_api.api.middleware.request_id import RequestIdMiddleware


class MiddlewareOptions(TypedDict, total=False):
    prometheus_enabled: bool
    prometheus_multiproc_dir: str | None


logger: structlog.stdlib.BoundLogger = structlog.get_logger()


def _create_prometheus_app(multiproc_dir: str | None) -> ASGIApp:
    from prometheus_client import make_asgi_app  # pyright: ignore[reportUnknownVariableType]

    app = make_asgi_app()  # pyright: ignore[reportUnknownVariableType]
    if multiproc_dir:
        from prometheus_client import (
            CollectorRegistry,
            multiprocess,
        )

        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        app = make_asgi_app(registry=registry)  # pyright: ignore[reportUnknownVariableType]

    return cast(ASGIApp, app)


def configure(app: FastAPI, **options: Unpack[MiddlewareOptions]) -> None:
    prometheus_enabled = options.get("prometheus_enabled", False)
    multiproc_dir = options.get("prometheus_multiproc_dir")

    app.add_middleware(
        RequestIdMiddleware,
        header_name="x-request-id",
        id_factory=lambda _: str(uuid.uuid4()),
    )

    if prometheus_enabled:
        logger.info("Prometheus middleware enabled")
        app.add_middleware(PrometheusMiddleware)
        metrics_app = _create_prometheus_app(multiproc_dir)

        app.mount("/metrics", metrics_app, name="prometheus")

    app.add_middleware(LoggingMiddleware)
