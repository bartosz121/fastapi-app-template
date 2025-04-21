import httpx
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.auth import AuthenticateAs
from tests.fixtures.database import SaveModel
from todo_api.core.exceptions import Codes
from todo_api.users import security
from todo_api.users.models import User

TEST_USERNAME = "testuser"
TEST_PASSWORD = "password123"
OTHER_USERNAME = "otheruser"
OTHER_PASSWORD = "otherpassword"


async def test_register_success(client: httpx.AsyncClient, session: AsyncSession):
    """Test successful user registration."""
    payload = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
    response = await client.post("/api/v1/users/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == TEST_USERNAME
    assert "id" in data

    db_user = await session.get(User, data["id"])
    assert db_user is not None
    assert db_user.username == TEST_USERNAME
    assert security.verify_password(TEST_PASSWORD, db_user.hashed_password)


async def test_register_username_conflict(
    client: httpx.AsyncClient, save_model_fixture: SaveModel
):
    """Test registration failure when username already exists."""
    existing_user = User(
        username=TEST_USERNAME, hashed_password=security.get_password_hash("somepassword")
    )
    await save_model_fixture(existing_user)

    payload = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
    response = await client.post("/api/v1/users/register", json=payload)

    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert "detail" in data
    assert "msg" in data["detail"]
    assert "Username already exists" in data["detail"]["msg"]
    assert data["detail"]["code"] == Codes.USERNAME_EXISTS


async def test_login_success(client: httpx.AsyncClient, save_model_fixture: SaveModel):
    """Test successful user login."""
    hashed_password = security.get_password_hash(TEST_PASSWORD)
    user = User(username=TEST_USERNAME, hashed_password=hashed_password)
    await save_model_fixture(user)

    payload = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
    response = await client.post("/api/v1/users/login", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "token" in data
    assert isinstance(data["token"], str)
    assert len(data["token"]) > 0

    assert "Set-Cookie" in response.headers


async def test_login_user_not_found(client: httpx.AsyncClient):
    """Test login failure when username does not exist."""
    payload = {"username": "nonexistentuser", "password": "password"}
    response = await client.post("/api/v1/users/login", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data
    assert "msg" in data["detail"]
    assert "Invalid username or password" in data["detail"]["msg"]
    assert data["detail"]["code"] == Codes.INVALID_USERNAME_OR_PASSWORD


async def test_login_incorrect_password(client: httpx.AsyncClient, save_model_fixture: SaveModel):
    """Test login failure with correct username but incorrect password."""
    hashed_password = security.get_password_hash(TEST_PASSWORD)
    user = User(username=TEST_USERNAME, hashed_password=hashed_password)
    await save_model_fixture(user)

    payload = {"username": TEST_USERNAME, "password": "wrongpassword"}
    response = await client.post("/api/v1/users/login", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data
    assert "msg" in data["detail"]
    assert "Invalid username or password" in data["detail"]["msg"]
    assert data["detail"]["code"] == Codes.INVALID_USERNAME_OR_PASSWORD


@pytest.mark.auth(AuthenticateAs(type_="dont_override"))
async def test_get_me_success(client: httpx.AsyncClient, save_model_fixture: SaveModel):
    """Test getting current user info when authenticated."""

    hashed_password = security.get_password_hash(TEST_PASSWORD)
    user = User(username=TEST_USERNAME, hashed_password=hashed_password)
    await save_model_fixture(user)

    login_payload = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
    login_response = await client.post("/api/v1/users/login", json=login_payload)
    assert login_response.status_code == status.HTTP_200_OK

    token = login_response.json()["token"]

    response = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == TEST_USERNAME
    assert data["id"] == user.id


async def test_get_me_unauthenticated(client: httpx.AsyncClient):
    """Test getting current user info fails when not authenticated."""
    response = await client.get("/api/v1/users/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_logout_success(client: httpx.AsyncClient, save_model_fixture: SaveModel):
    """Test successful user logout."""

    hashed_password = security.get_password_hash(TEST_PASSWORD)
    user = User(username=TEST_USERNAME, hashed_password=hashed_password)
    await save_model_fixture(user)
    login_payload = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
    login_response = await client.post("/api/v1/users/login", json=login_payload)
    assert login_response.status_code == status.HTTP_200_OK

    response = await client.get("/api/v1/users/logout")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == {"status": "ok"}

    assert "Set-Cookie" in response.headers

    assert (
        "Max-Age=0" in response.headers["Set-Cookie"]
        or "expires=" in response.headers["Set-Cookie"].lower()
    )

    me_response = await client.get("/api/v1/users/me")
    assert me_response.status_code == status.HTTP_401_UNAUTHORIZED
