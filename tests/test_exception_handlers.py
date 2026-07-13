import httpx
import pytest
from fastapi import FastAPI, status
from pydantic import BaseModel

from todo_api.api.exception_handlers import configure as configure_exception_handlers
from todo_api.core.database.exceptions import (
    DatabaseError,
    DatabaseOperationError,
    IntegrityConstraintError,
    RecordNotFoundError,
)
from todo_api.core.exceptions import ApplicationError


@pytest.mark.asyncio
async def test_request_validation_error_handler(client: httpx.AsyncClient):
    class Item(BaseModel):
        name: str
        price: float

    app = FastAPI()

    @app.post("/items/request_validation", response_model=Item)
    async def create_item(item: Item):  # pyright: ignore[reportUnusedFunction]
        return item

    configure_exception_handlers(app)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/items/request_validation", json={"name": "Test"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        data = response.json()
        assert data["error"] == "Unprocessable Entity"
        assert data["code"] == "REQUEST_VALIDATION_ERROR"
        assert "detail" in data
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0
        assert data["detail"][0]["loc"] == ["body", "price"]
        assert data["detail"][0]["msg"] == "Field required"


@pytest.mark.asyncio
async def test_response_validation_error_handler(client: httpx.AsyncClient):
    class Item(BaseModel):
        name: str
        price: float

    app = FastAPI()

    @app.get("/items/response_validation", response_model=Item)
    async def get_item():  # pyright: ignore[reportUnusedFunction]
        # This will cause a ResponseValidationError because 'price' is missing
        return {"name": "Invalid Item"}

    configure_exception_handlers(app)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/items/response_validation")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        data = response.json()
        assert data["error"] == "Response Validation Error"
        assert data["code"] == "RESPONSE_VALIDATION_ERROR"
        assert data["detail"] is None


@pytest.mark.asyncio
async def test_database_error_handlers(client: httpx.AsyncClient):
    app = FastAPI()

    @app.get("/not-found")
    async def not_found():  # pyright: ignore[reportUnusedFunction]
        raise RecordNotFoundError("No record found")

    @app.get("/conflict")
    async def conflict():  # pyright: ignore[reportUnusedFunction]
        raise IntegrityConstraintError("Duplicate key")

    @app.get("/database-error")
    async def database_error():  # pyright: ignore[reportUnusedFunction]
        raise DatabaseOperationError("Database unavailable")

    @app.get("/database-base-error")
    async def database_base_error():  # pyright: ignore[reportUnusedFunction]
        raise DatabaseError("Database unavailable")

    @app.get("/application-error")
    async def application_error():  # pyright: ignore[reportUnusedFunction]
        raise ApplicationError("Application failed")

    configure_exception_handlers(app)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/not-found")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "No record found"

        response = await client.get("/conflict")
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"] == "Duplicate key"

        response = await client.get("/database-error")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] is None

        response = await client.get("/database-base-error")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] is None

        response = await client.get("/application-error")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] is None
