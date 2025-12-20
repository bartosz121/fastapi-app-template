from collections.abc import AsyncGenerator, Generator
from typing import Annotated, Any

from fastapi import Depends
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from todo_api.core.database.base import AsyncSessionMaker, SyncSessionMaker
from todo_api.core.service.sqlalchemy import SQLAlchemyService as SQLAlchemyService_


def get_session(request: Request) -> Generator[Session, Any]:
    if session := getattr(request.state, "session", None):
        yield session
    else:
        with SyncSessionMaker() as session:
            try:
                request.state.session = session
                yield session
            except:
                session.rollback()
                raise
            else:
                session.commit()


DbSession = Annotated[Session, Depends(get_session)]


async def get_async_session(request: Request) -> AsyncGenerator[AsyncSession, Any]:
    if session := getattr(request.state, "async_session", None):
        yield session
    else:
        async with AsyncSessionMaker() as session:
            try:
                request.state.async_session = session
                yield session
            except:
                await session.rollback()
                raise
            else:
                await session.commit()


AsyncDbSession = Annotated[AsyncSession, Depends(get_async_session)]


async def get_sqlalchemy_service(session: AsyncDbSession) -> SQLAlchemyService_:
    return SQLAlchemyService_(session)


SQLAlchemyService = Annotated[SQLAlchemyService_, Depends(get_sqlalchemy_service)]

__all__ = (
    "get_session",
    "DbSession",
    "AsyncDbSession",
    "SQLAlchemyService",
)
