from fastapi import APIRouter, status
from fastapi.requests import Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

router = APIRouter()


@router.get("/metrics", include_in_schema=False)
def handle_metrics(request: Request):
    headers = {"Content-Type": CONTENT_TYPE_LATEST}
    return Response(
        generate_latest(REGISTRY),
        status_code=status.HTTP_200_OK,
        headers=headers,
    )
