from collections.abc import Awaitable, Callable, Collection
from functools import partial
from typing import Any, ClassVar

from opentelemetry import trace
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.trace import Span, SpanKind, Tracer
from wrapt import (  # pyright: ignore[reportMissingTypeStubs]
    wrap_function_wrapper,  # pyright: ignore[reportUnknownVariableType]
)

from todo_api.core.service.sqlalchemy import SQLAlchemyService
from todo_api.version import __version__

INSTRUMENTED_PUBLIC_METHODS = {
    "count",
    "create",
    "delete",
    "exists",
    "get",
    "get_one",
    "get_one_or_none",
    "list",
    "list_and_count",
    "update",
}


def _extract_attributes_from_public_methods(
    instance: SQLAlchemyService[Any, Any],
    args: tuple[Any],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Extracts span attributes from SQLAlchemyService method calls.

    Extracts record identification and model type for observability context.

    :param instance: The SQLAlchemyService instance
    :type instance: Any
    :param args: Positional arguments (excluding self)
    :type args: tuple[Any]
    :param kwargs: Keyword arguments
    :type kwargs: dict[str, Any]
    :return: Dictionary of span attributes
    :rtype: dict[str, Any]
    """
    attrs: dict[str, Any] = {}

    # Extract model_type from service instance
    if hasattr(instance, "model"):
        attrs["model_type"] = instance.model.__name__

    # Extract record_id from id argument
    if "id" in kwargs:
        attrs["record_id"] = str(kwargs["id"])
    elif len(args) > 0 and isinstance(args[0], (int, str)):
        attrs["record_id"] = str(args[0])

    # Extract model_type and record_id from data argument
    if "data" in kwargs:
        data = kwargs["data"]
    elif (
        len(args) > 0
        and hasattr(args[0], "__class__")
        and not isinstance(args[0], (int, str, bool))
    ):
        data = args[0]
    else:
        data = None

    if data is not None:
        attrs["model_type"] = data.__class__.__name__
        # Try to extract id from model instance for better record tracking
        if hasattr(data, "id"):
            try:
                attrs["record_id"] = str(data.id)
            except (AttributeError, TypeError):
                pass

    # Extract session behavior overrides
    if "auto_commit" in kwargs and kwargs["auto_commit"] is not None:
        attrs["auto_commit"] = kwargs["auto_commit"]
    if "auto_refresh" in kwargs and kwargs["auto_refresh"] is not None:
        attrs["auto_refresh"] = kwargs["auto_refresh"]
    if "auto_expunge" in kwargs and kwargs["auto_expunge"] is not None:
        attrs["auto_expunge"] = kwargs["auto_expunge"]

    return attrs


def _apply_attrs_to_span(span: Span, attrs: dict[str, Any]) -> None:
    for key, value in attrs.items():
        span.set_attribute(key, value)


class SQLAlchemyServiceInstrumentator(BaseInstrumentor):
    _module_name: ClassVar[str] = "SQLAlchemyService"
    _version: ClassVar[str] = __version__

    def __init__(self) -> None:
        super().__init__()

    def instrumentation_dependencies(self) -> Collection[str]:
        return (f"todo_api == {__version__}",)

    def _instrument(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Instruments `todo_api.core.service.sqlalchemy.SQLAlchemyService`

        Args:
            **kwargs: Optional arguments
                ``tracer_provider``: a TracerProvider, defaults to global
                ``meter_provider``: a MeterProvider, defaults to global
        """
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
        instance: Any,  # `SQLAlchemyService` instance  # noqa: ANN401
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        tracer: Tracer,
        method_name: str,
    ) -> Any:  # noqa: ANN401
        with tracer.start_as_current_span(method_name, kind=SpanKind.INTERNAL) as span:
            if span.is_recording():
                span_attrs = _extract_attributes_from_public_methods(instance, args, kwargs)
                _apply_attrs_to_span(span, span_attrs)

            try:
                return await wrapped(*args, **kwargs)
            except Exception as exc:
                span.record_exception(exc)
                span.set_attribute("error", True)
                raise
