from advanced_alchemy.config.asyncio import AlembicAsyncConfig
from advanced_alchemy.config.sync import AlembicSyncConfig
from advanced_alchemy.extensions.fastapi import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemySyncConfig,
    SyncSessionConfig,
)

from todo_api.core.config import settings

sqlalchemy_async_config = SQLAlchemyAsyncConfig(
    connection_string=settings.get_sqlite_dsn(driver="aiosqlite"),
    session_config=AsyncSessionConfig(expire_on_commit=False),
    alembic_config=AlembicAsyncConfig(
        script_config="/home/bartosz/code/fastapi-sandbox/alembic.ini",
        script_location="/home/bartosz/code/fastapi-sandbox/migrations",
    ),
    commit_mode="autocommit",
)
sqlalchemy_sync_config = SQLAlchemySyncConfig(
    connection_string=settings.get_sqlite_dsn(),
    session_config=SyncSessionConfig(expire_on_commit=False),
    alembic_config=AlembicSyncConfig(
        script_config="/home/bartosz/code/fastapi-sandbox/alembic.ini",
        script_location="/home/bartosz/code/fastapi-sandbox/migrations",
    ),
    commit_mode="autocommit",
)
