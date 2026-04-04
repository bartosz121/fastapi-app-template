import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from tests.fixtures.database import SaveModel
from todo_api.users.models import User
from todo_api.users.security import get_password_hash


async def _count_users(session: AsyncSession) -> int:
    user_count = await session.scalar(select(func.count()).select_from(User))
    assert user_count is not None
    return user_count


async def test_session_uses_cloned_database(session: AsyncSession) -> None:
    current_database = await session.scalar(text("SELECT current_database()"))

    assert current_database is not None
    assert current_database.startswith("test_db_")


async def test_cloned_database_starts_clean(
    session: AsyncSession, save_model_fixture: SaveModel
) -> None:
    assert await _count_users(session) == 0

    user = User(
        username=f"db-clone-{uuid.uuid4().hex}",
        hashed_password=get_password_hash("password123"),
    )
    await save_model_fixture(user)

    assert await _count_users(session) == 1


async def test_engine_and_session_use_same_cloned_database(
    session: AsyncSession, engine: AsyncEngine
) -> None:
    session_database_name = await session.scalar(text("SELECT current_database()"))

    async with engine.connect() as conn:
        engine_database_name = await conn.scalar(text("SELECT current_database()"))

    assert session_database_name == engine_database_name


async def test_same_username_isolated_across_tests_first(
    session: AsyncSession, save_model_fixture: SaveModel
) -> None:
    """Run with 1 worker and verify this shared username does not collide across tests."""
    user = User(
        username="shared-template-username",
        hashed_password=get_password_hash("password123"),
    )
    await save_model_fixture(user)

    assert await _count_users(session) == 1


async def test_same_username_isolated_across_tests_second(
    session: AsyncSession, save_model_fixture: SaveModel
) -> None:
    """Run with 1 worker and verify this shared username does not collide across tests."""
    user = User(
        username="shared-template-username",
        hashed_password=get_password_hash("password123"),
    )
    await save_model_fixture(user)

    assert await _count_users(session) == 1
