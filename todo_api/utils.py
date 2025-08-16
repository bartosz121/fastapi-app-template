from datetime import datetime
from http import HTTPStatus
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    return datetime.now(tz=ZoneInfo("UTC"))


def get_http_status_message(code: int) -> str:
    return HTTPStatus(code).phrase
