from datetime import timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.auth import AuthenticateAs
from tests.fixtures.database import SaveModel
from todo_api.auth.models import UserSession
from todo_api.core.config import settings
from todo_api.users.models import User
from todo_api.users.security import get_password_hash
from todo_api.utils import utc_now

TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword"


@pytest.mark.auth(AuthenticateAs(type_="dont_override"))
async def test_session_creation_on_login(
    client: httpx.AsyncClient,
    session: AsyncSession,
    save_model_fixture: SaveModel,
):
    hashed_password = get_password_hash(TEST_PASSWORD)
    user = User(username=TEST_USERNAME, hashed_password=hashed_password)
    await save_model_fixture(user)

    login_payload = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
    response = await client.post("/api/v1/users/login", json=login_payload)

    assert response.status_code == status.HTTP_200_OK
    assert "token" in response.json()

    # Verify session was created in the database
    session_token = response.json()["token"]
    user_session = (
        await session.execute(
            select(UserSession).where(UserSession.session_token == session_token)
        )
    ).scalar_one_or_none()
    assert user_session is not None
    assert user_session.user_id == user.id
    expires_at_aware = user_session.expires_at
    # TODO: This timezone handling is specific to SQLite
    # Remove if moving to a different database (e.g., PostgreSQL),
    if expires_at_aware.tzinfo is None:
        expires_at_aware = expires_at_aware.replace(tzinfo=ZoneInfo("UTC"))
    assert expires_at_aware > utc_now()


@pytest.mark.auth(AuthenticateAs(type_="dont_override"))
async def test_session_validation_with_cookie(
    client: httpx.AsyncClient,
    session: AsyncSession,
    save_model_fixture: SaveModel,
):
    hashed_password = get_password_hash(TEST_PASSWORD)
    user = User(username=TEST_USERNAME, hashed_password=hashed_password)
    await save_model_fixture(user)

    # Manually create a session and set the cookie
    expires_at = utc_now() + settings.get_user_session_ttl_timedelta()
    user_session = UserSession(user_id=user.id, expires_at=expires_at)
    session.add(user_session)
    await session.commit()
    await session.refresh(user_session)

    client.cookies.set(settings.AUTH_COOKIE_NAME, user_session.session_token)

    response = await client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == TEST_USERNAME


@pytest.mark.auth(AuthenticateAs(type_="dont_override"))
async def test_session_validation_with_bearer_token(
    client: httpx.AsyncClient,
    session: AsyncSession,
    save_model_fixture: SaveModel,
):
    hashed_password = get_password_hash(TEST_PASSWORD)
    user = User(username=TEST_USERNAME, hashed_password=hashed_password)
    await save_model_fixture(user)

    # Manually create a session
    expires_at = utc_now() + settings.get_user_session_ttl_timedelta()
    user_session = UserSession(user_id=user.id, expires_at=expires_at)
    session.add(user_session)
    await session.commit()
    await session.refresh(user_session)

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_session.session_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == TEST_USERNAME


@pytest.mark.auth(AuthenticateAs(type_="dont_override"))
async def test_expired_session_is_invalid(
    client: httpx.AsyncClient,
    session: AsyncSession,
    save_model_fixture: SaveModel,
):
    hashed_password = get_password_hash(TEST_PASSWORD)
    user = User(username=TEST_USERNAME, hashed_password=hashed_password)
    await save_model_fixture(user)

    # Create an expired session
    expired_at = utc_now() - timedelta(seconds=1)
    user_session = UserSession(user_id=user.id, expires_at=expired_at)
    session.add(user_session)
    await session.commit()
    await session.refresh(user_session)

    client.cookies.set(settings.AUTH_COOKIE_NAME, user_session.session_token)

    response = await client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth(AuthenticateAs(type_="dont_override"))
async def test_logout_deletes_session(
    client: httpx.AsyncClient,
    session: AsyncSession,
    save_model_fixture: SaveModel,
):
    hashed_password = get_password_hash(TEST_PASSWORD)
    user = User(username=TEST_USERNAME, hashed_password=hashed_password)
    await save_model_fixture(user)

    login_payload = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
    login_response = await client.post("/api/v1/users/login", json=login_payload)
    assert login_response.status_code == status.HTTP_200_OK

    session_token = login_response.json()["token"]
    client.cookies.set(settings.AUTH_COOKIE_NAME, session_token)

    # Ensure session exists before logout
    initial_session = (
        await session.execute(
            select(UserSession).where(UserSession.session_token == session_token)
        )
    ).scalar_one_or_none()
    assert initial_session is not None

    logout_response = await client.get("/api/v1/users/logout")
    assert logout_response.status_code == status.HTTP_200_OK
    assert logout_response.json() == {"status": "ok"}

    # Verify session is deleted from the database
    deleted_session = (
        await session.execute(
            select(UserSession).where(UserSession.session_token == session_token)
        )
    ).scalar_one_or_none()
    await session.commit()
    await session.flush()
    assert deleted_session is None

    # Verify user is no longer authenticated
    response_after_logout = await client.get("/api/v1/users/me")
    assert response_after_logout.status_code == status.HTTP_401_UNAUTHORIZED
