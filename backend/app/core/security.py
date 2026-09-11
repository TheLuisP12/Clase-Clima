"""Utilidades de seguridad: hashing de contraseñas y generación/verificación de JWT.

Nada en este módulo debe loguear contraseñas en texto plano, hashes ni tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# bcrypt es el esquema recomendado por el spec (hash, no texto plano).
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verifica una contraseña contra su hash almacenado.

    Nunca lanza con detalle del motivo del fallo; retorna simplemente
    True/False para que la capa de servicio use un mensaje genérico.
    """
    try:
        return _pwd_context.verify(plain_password, password_hash)
    except (ValueError, TypeError):
        # Hash corrupto/formato inesperado: se trata como credencial inválida.
        return False


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """Crea un JWT firmado (HS256 por defecto) con el email como subject."""
    expire_delta = timedelta(minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES)
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + expire_delta,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decodifica y valida un JWT. Retorna None si es inválido/expirado."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
