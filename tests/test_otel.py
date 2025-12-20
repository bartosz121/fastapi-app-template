import json

import pytest

from todo_api.core.config import Environment


async def test_logging_adds_trace_context(capsys: pytest.CaptureFixture[str]):
    """Test that structlog context includes span_id and trace_id in request logs"""
    import httpx
    import structlog
    from fastapi import FastAPI

    from todo_api.core.logging import configure as configure_logging
    from todo_api.instrumentation import configure as configure_instrumentation

    configure_instrumentation(
        app_name="test-app",
        app_version="0.0.0",
        app_environment=Environment.TESTING,
        otlp_endpoint="127.0.0.1:4317",
        otlp_endpoint_insecure=True,
    )

    configure_logging(
        log_level="DEBUG",
        # PRODUCTION so logs are sent as json - easier to assert below
        environment=Environment.PRODUCTION,
        enabled_loggers=[],
    )

    from opentelemetry.instrumentation.fastapi import (  # pyright: ignore[reportMissingTypeStubs]
        FastAPIInstrumentor,
    )

    from todo_api.core.middleware.logging import LoggingMiddleware

    app = FastAPI()
    app.add_middleware(LoggingMiddleware)

    FastAPIInstrumentor.instrument_app(app)

    logger: structlog.stdlib.BoundLogger = structlog.get_logger()

    @app.get("/test")
    async def test_endpoint():  # pyright: ignore[reportUnusedFunction]
        logger.info("test_log_message")
        return {"status": "ok"}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Request without parent span
        response = await client.get("/test")
        assert response.status_code == 200

    captured = capsys.readouterr()
    log_without_parent = captured.err.strip()
    log_dict_without_parent = json.loads(log_without_parent)

    assert log_dict_without_parent["span_id"] is not None
    assert log_dict_without_parent["trace_id"] is not None
    assert "parent_span_id" in log_dict_without_parent
    assert log_dict_without_parent["parent_span_id"] is None

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Request with parent span ID in W3C Trace Context header
        parent_trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
        parent_span_id = "00f067aa0ba902b7"
        headers = {"traceparent": f"00-{parent_trace_id}-{parent_span_id}-01"}
        response = await client.get("/test", headers=headers)
        assert response.status_code == 200

    captured = capsys.readouterr()
    log_with_parent = captured.err.strip()
    log_dict_with_parent = json.loads(log_with_parent)

    assert log_dict_with_parent["span_id"] is not None
    assert log_dict_with_parent["trace_id"] is not None
    assert "parent_span_id" in log_dict_with_parent
    assert log_dict_with_parent["trace_id"] == parent_trace_id
    assert log_dict_with_parent["parent_span_id"] == parent_span_id


async def test_sqlalchemy_service_instrumentation_adds_attributes():
    """Test that SQLAlchemy service method calls create spans with model/record attributes"""
    from opentelemetry import trace
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from sqlalchemy import MetaData
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.orm import Mapped, declarative_base, mapped_column

    from todo_api.core.service.sqlalchemy import SQLAlchemyService
    from todo_api.opentelemetry.sqlalchemy_service import SQLAlchemyServiceInstrumentator

    provider = trace.get_tracer_provider()

    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)  # type: ignore

    # Clean up any previous instrumentation and instrument
    try:
        SQLAlchemyServiceInstrumentator().uninstrument()
    except Exception:
        pass

    SQLAlchemyServiceInstrumentator().instrument(tracer_provider=provider)

    metadata = MetaData()
    Base = declarative_base(metadata=metadata)

    class TestModel(Base):
        __tablename__ = "test_models_otel"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    class TestService(SQLAlchemyService[TestModel, int]):
        model = TestModel

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with sessionmaker() as session:
            instance = TestModel(id=1, name="test")
            session.add(instance)
            await session.commit()

            service = TestService(session)

            tracer = provider.get_tracer(__name__)

            with tracer.start_as_current_span("test_service_call"):
                await service.get_one(id=1)

            spans = exporter.get_finished_spans()

            service_spans = [s for s in spans if s.name == "get_one"]
            assert len(service_spans) > 0, "No 'get_one' span found"

            span_attrs = service_spans[0].attributes
            assert span_attrs

            assert "model_type" in span_attrs
            assert span_attrs["model_type"] == "TestModel"
            assert "record_id" in span_attrs
            assert span_attrs["record_id"] == "1"
    finally:
        SQLAlchemyServiceInstrumentator().uninstrument()
        await engine.dispose()
