from collections.abc import Awaitable, Callable, Collection
from functools import partial
from typing import Any, ClassVar

from opentelemetry import trace
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.trace import SpanKind, Tracer
from wrapt import (  # pyright: ignore[reportMissingTypeStubs]
    wrap_function_wrapper,  # pyright: ignore[reportUnknownVariableType]
)

from todo_api.core.service.sqlalchemy import SQLAlchemyService
from todo_api.version import __version__

INSTRUMENTED_PUBLIC_METHODS = {
    "execute_one",
    "execute_one_or_none",
    "execute_list",
    "execute_rows",
    "execute_list_and_count",
}


class SQLAlchemyServiceInstrumentator(BaseInstrumentor):
    _module_name: ClassVar[str] = "SQLAlchemyService"
    _version: ClassVar[str] = __version__

    def instrumentation_dependencies(self) -> Collection[str]:
        return (f"todo_api == {__version__}",)

    def _instrument(self, **kwargs: Any) -> None:  # noqa: ANN401
        tracer_provider = kwargs.get("tracer_provider")
        tracer = trace.get_tracer(
            self._module_name,
            self._version,
            tracer_provider,
            schema_url="https://opentelemetry.io/schemas/1.11.0",
        )

        for method_name in INSTRUMENTED_PUBLIC_METHODS:
            wrap_function_wrapper(
                "todo_api.core.service.sqlalchemy",
                f"SQLAlchemyService.{method_name}",
                partial(
                    self._async_method_wrapper,
                    tracer=tracer,
                    method_name=method_name,
                ),
            )

    def _uninstrument(self, **kwargs: Any) -> None:  # noqa: ANN401
        for method_name in INSTRUMENTED_PUBLIC_METHODS:
            unwrap(SQLAlchemyService, method_name)

    @staticmethod
    async def _async_method_wrapper(
        wrapped: Callable[..., Awaitable[Any]],
        instance: Any,  # SQLAlchemyService instance  # noqa: ANN401
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        tracer: Tracer,
        method_name: str,
    ) -> Any:  # noqa: ANN401
        with tracer.start_as_current_span(method_name, kind=SpanKind.INTERNAL) as span:
            try:
                return await wrapped(*args, **kwargs)
            except Exception as exc:
                span.record_exception(exc)
                span.set_attribute("error", True)
                raise
