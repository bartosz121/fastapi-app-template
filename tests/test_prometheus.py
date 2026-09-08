from collections.abc import Mapping

import httpx
from fastapi import APIRouter, FastAPI, status
from prometheus_client import REGISTRY, Gauge
from prometheus_client.parser import text_string_to_metric_families

from todo_api.api.middleware import configure as configure_middleware
from todo_api.api.middleware.configure import (
    _create_prometheus_app,  # pyright: ignore[reportPrivateUsage]
)
from todo_api.api.middleware.prometheus import PrometheusMiddleware


def get_registry_value(metric_name: str, labels: Mapping[str, str]) -> float:
    for family in REGISTRY.collect():
        for sample in family.samples:
            if sample.name == metric_name and sample.labels == labels:
                return sample.value
    return 0.0


async def test_prometheus_middleware_records_successful_request():
    app = FastAPI()
    app.add_middleware(PrometheusMiddleware)

    @app.get("/users/{user_id}")
    async def get_user(user_id: int) -> dict[str, int]:  # pyright: ignore[reportUnusedFunction]
        return {"id": user_id}

    labels = {"method": "GET", "path": "/users/{user_id}"}
    request_count_before = get_registry_value("todo_api_requests_total", labels)
    response_count_before = get_registry_value(
        "todo_api_responses_total", {**labels, "status_code": "200"}
    )
    histogram_count_before = get_registry_value(
        "todo_api_requests_process_time_seconds_count", {**labels, "status_code": "200"}
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/users/42")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 42}
    assert get_registry_value("todo_api_requests_total", labels) == request_count_before + 1
    assert (
        get_registry_value("todo_api_responses_total", {**labels, "status_code": "200"})
        == response_count_before + 1
    )
    assert (
        get_registry_value(
            "todo_api_requests_process_time_seconds_count", {**labels, "status_code": "200"}
        )
        == histogram_count_before + 1
    )
    assert get_registry_value("todo_api_requests_in_progress", labels) == 0


async def test_prometheus_middleware_handles_nested_router():
    """
    As of FastAPI 0.137 routes from child routers added with `include_router`
    are no longer flattened into `app.routes`, triggering:

    ```
    AttributeError: '_IncludedRouter' object has no attribute 'path'
    ```
    """
    app = FastAPI()
    app.add_middleware(PrometheusMiddleware)

    child_router = APIRouter()

    @child_router.get("/items/{item_id}")
    async def get_item(item_id: int) -> dict[str, int]:  # pyright: ignore[reportUnusedFunction]
        return {"id": item_id}

    parent_router = APIRouter()
    parent_router.include_router(child_router)
    app.include_router(parent_router, prefix="/api")

    labels = {"method": "GET", "path": "/api/items/{item_id}"}
    request_count_before = get_registry_value("todo_api_requests_total", labels)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/items/42")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 42}
    assert get_registry_value("todo_api_requests_total", labels) == request_count_before + 1


async def test_prometheus_middleware_records_unhandled_exception():
    app = FastAPI()
    app.add_middleware(PrometheusMiddleware)

    @app.get("/fail")
    async def fail() -> None:  # pyright: ignore[reportUnusedFunction]
        raise RuntimeError("error")

    labels = {"method": "GET", "path": "/fail"}
    exception_labels = {**labels, "exception_type": "RuntimeError"}
    response_labels = {**labels, "status_code": "500"}
    exception_count_before = get_registry_value("todo_api_exceptions_total", exception_labels)
    response_count_before = get_registry_value("todo_api_responses_total", response_labels)
    histogram_count_before = get_registry_value(
        "todo_api_requests_process_time_seconds_count", response_labels
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.get("/fail")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert (
        get_registry_value("todo_api_exceptions_total", exception_labels)
        == exception_count_before + 1
    )
    assert (
        get_registry_value("todo_api_responses_total", response_labels)
        == response_count_before + 1
    )
    assert (
        get_registry_value("todo_api_requests_process_time_seconds_count", response_labels)
        == histogram_count_before + 1
    )
    assert get_registry_value("todo_api_requests_in_progress", labels) == 0


async def test_configure_mounts_metrics_when_prometheus_is_enabled():
    app = FastAPI()
    configure_middleware(app, prometheus_enabled=True)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/metrics/")

    assert response.status_code == status.HTTP_200_OK


async def test_metrics_endpoint_returns_prometheus_exposition():
    metric = Gauge("test_metrics_endpoint_value", "Value used by the metrics endpoint test")
    metric.set(7)

    app = FastAPI()
    app.mount("/metrics", _create_prometheus_app(None), name="prometheus")

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/metrics/")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"].startswith("text/plain; version=")

        families = {
            family.name: family for family in text_string_to_metric_families(response.text)
        }
        assert families["test_metrics_endpoint_value"].samples[0].value == 7
    finally:
        REGISTRY.unregister(metric)
