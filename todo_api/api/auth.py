from fastapi.responses import Response


def get_bearer_token(authorization: str | None) -> str | None:
    if authorization:
        try:
            scheme, token = authorization.split()
            if scheme.lower() == "bearer":
                return token
        except ValueError:
            pass
    return None


def set_auth_cookie(
    response: Response,
    value: str,
    *,
    auth_cookie_name: str,
    auth_cookie_domain: str,
    expires_in: int,
    secure: bool,
) -> None:
    response.set_cookie(
        auth_cookie_name,
        value=value,
        expires=expires_in,
        path="/",
        domain=auth_cookie_domain,
        httponly=True,
        secure=secure,
        samesite="lax",
    )


def clear_auth_cookie(
    response: Response,
    *,
    auth_cookie_name: str,
    auth_cookie_domain: str,
    secure: bool,
) -> None:
    response.set_cookie(
        auth_cookie_name,
        value="",
        expires=0,
        path="/",
        domain=auth_cookie_domain,
        httponly=True,
        secure=secure,
        samesite="lax",
    )
