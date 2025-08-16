from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from todo_api.core.database.aa_config import alchemy_async, alchemy_sync

DbSession = Annotated[Session, Depends(alchemy_sync.provide_session())]

AsyncDbSession = Annotated[AsyncSession, Depends(alchemy_async.provide_session())]

__all__ = (
    "DbSession",
    "AsyncDbSession",
)
