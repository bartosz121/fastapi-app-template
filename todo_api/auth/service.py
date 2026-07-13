from datetime import datetime, timedelta

from todo_api.auth.models import UserSession
from todo_api.core.database.service import SQLAlchemyModelService
from todo_api.utils import utc_now


class UserSessionService(SQLAlchemyModelService[UserSession, int]):
    model = UserSession


def create_user_session_expires_at(*, ttl: timedelta) -> datetime:
    return utc_now() + ttl
