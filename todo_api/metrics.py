from fastapi import APIRouter, status
from fastapi.requests import Request
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    generate_latest,
    multiprocess,
)

from todo_api.core.config import settings

router = APIRouter()


@router.get("/metrics", include_in_schema=False)
def handle_metrics(request: Request) -> Response:
    headers = {"Content-Type": CONTENT_TYPE_LATEST}
    registry = REGISTRY

    if settings.PROMETHEUS_MULTIPROC_DIR:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)

    return Response(
        generate_latest(registry),
        status_code=status.HTTP_200_OK,
        headers=headers,
    )
