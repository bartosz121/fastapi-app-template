import httpx
import pytest
from fastapi import FastAPI, status
from pydantic import BaseModel

from todo_api.core.exception_handlers import configure as configure_exception_handlers


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

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
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

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["error"] == "Response Validation Error"
        assert data["code"] == "RESPONSE_VALIDATION_ERROR"
        assert data["detail"] is None
