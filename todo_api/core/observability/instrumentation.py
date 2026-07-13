from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from todo_api.core.config import Environment


def configure(
    *,
    app_name: str,
    app_version: str,
    app_environment: Environment,
    otlp_endpoint: str,
    otlp_endpoint_insecure: bool,
) -> None:
    import structlog
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import (
        TraceIdRatioBased,
        _AlwaysOn,  # pyright: ignore[reportPrivateUsage]
    )

    logger: structlog.stdlib.BoundLogger = structlog.get_logger()

    resource = Resource(
        attributes={
            "service.name": app_name,
            "service.version": app_version,
            "deployment.environment": app_environment,
        },
    )

    sampler = TraceIdRatioBased(1 / 10) if app_environment == "PRODUCTION" else _AlwaysOn(None)

    provider = TracerProvider(resource=resource, sampler=sampler)

    if app_environment == "TESTING":
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

        exporter = InMemorySpanExporter()
        processor = SimpleSpanProcessor(exporter)
    else:
        exporter = OTLPSpanExporter(otlp_endpoint, insecure=otlp_endpoint_insecure)
        processor = BatchSpanProcessor(
            exporter,
            max_queue_size=2048,
            schedule_delay_millis=5000,
        )

    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    logger.info(f"Opentelemetry tracer provider with {exporter.__class__.__name__!r} initialized")
