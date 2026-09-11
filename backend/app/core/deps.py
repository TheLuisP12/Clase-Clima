"""Dependencias FastAPI compartidas para proteger endpoints con JWT."""

from fastapi import Header, HTTPException, status

from app.core.security import decode_access_token

INVALID_TOKEN_MESSAGE = "Not authenticated"


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=INVALID_TOKEN_MESSAGE,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_email(authorization: str | None = Header(default=None)) -> str:
    """Extrae y valida el JWT del header `Authorization: Bearer <token>`.

    Retorna el email (subject) del usuario autenticado. Lanza 401 si el
    header falta, tiene formato inválido, o el token es inválido/expirado.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise _unauthorized()

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise _unauthorized()

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise _unauthorized()

    return payload["sub"]
