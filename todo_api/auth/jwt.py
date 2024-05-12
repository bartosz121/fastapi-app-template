from datetime import datetime
from typing import Any

import jwt

ALGORITHM = "HS256"


def encode(*, data: dict[str, Any], secret: str, expires_at: datetime) -> str:
    data_to_encode = data.copy()
    data_to_encode["expires_at"] = int(expires_at.timestamp())

    return jwt.encode(data_to_encode, secret, algorithm=ALGORITHM)


def decode(*, token: str, secret: str) -> dict[str, Any]:
    return jwt.decode(token, secret, algorithms=[ALGORITHM])
