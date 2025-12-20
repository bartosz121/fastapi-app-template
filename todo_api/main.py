from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict, cast

from fastapi import FastAPI

from todo_api.api import router_v1
from todo_api.core.config import settings
from todo_api.core.exception_handlers import configure as configure_exception_handlers
from todo_api.core.logging import configure as configure_logging
from todo_api.core.middleware import configure as configure_middleware
from todo_api.version import __version__

if settings.OTEL_ENABLED:
    from todo_api.instrumentation import configure as configure_instrumentation

    configure_instrumentation(
        app_name=settings.APP_NAME,
        app_version=__version__,
        app_environment=settings.ENVIRONMENT,
        otlp_endpoint=settings.OTLP_GRPC_ENDPOINT,
        otlp_endpoint_insecure=settings.OTLP_EXPORTER_INSECURE,
    )


class State(TypedDict):
    auth_cookie_name: str
    auth_cookie_domain: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    yield {
        "auth_cookie_name": settings.AUTH_COOKIE_NAME,
        "auth_cookie_domain": settings.AUTH_COOKIE_DOMAIN,
    }

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider

    provider = cast(TracerProvider, trace.get_tracer_provider())
    provider.force_flush(timeout_millis=5000)


def create_app() -> FastAPI:
    from opentelemetry.instrumentation.fastapi import (  # pyright: ignore[reportMissingTypeStubs]
        FastAPIInstrumentor,
    )

    from todo_api.core.config import settings
    from todo_api.core.exceptions import ResponseValidationError
    from todo_api.opentelemetry.sqlalchemy_model_service import (
        SQLAlchemyModelServiceInstrumentator,
    )
    from todo_api.opentelemetry.sqlalchemy_service import SQLAlchemyServiceInstrumentator
    from todo_api.version import __version__

    configure_logging(settings.LOG_LEVEL, settings.ENVIRONMENT, settings.ENABLED_LOGGERS)

    SQLAlchemyServiceInstrumentator().instrument()
    SQLAlchemyModelServiceInstrumentator().instrument()

    app = FastAPI(
        title=settings.APP_NAME,
        version=__version__,
        lifespan=lifespan,
        # Override default validation error schema
        responses={
            422: {"description": "Response Validation Error", "model": ResponseValidationError}
        },
    )

    configure_middleware(app, settings.ENVIRONMENT)
    configure_exception_handlers(app)

    @app.get("/health")
    async def health():  # pyright: ignore[reportUnusedFunction] # noqa: ANN202
        return {"msg": "ok"}

    app.include_router(router_v1, prefix="/api")

    FastAPIInstrumentor.instrument_app(app)

    return app
