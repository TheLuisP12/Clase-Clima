"""Lógica de negocio de autenticación.

Regla de seguridad clave (criterio de aceptación del spec): si el usuario no
existe O la contraseña no coincide, se lanza EXACTAMENTE la misma excepción
con el mismo mensaje genérico, para no revelar si un correo está registrado.
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse

logger = logging.getLogger("app.auth")

# Mensaje único para credenciales inválidas, sin importar la causa real.
INVALID_CREDENTIALS_MESSAGE = "Invalid email or password"


def _invalid_credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=INVALID_CREDENTIALS_MESSAGE,
    )


class AuthService:
    def __init__(self, db: Session, repository: UserRepository | None = None) -> None:
        # El repositorio puede inyectarse (p.ej. en tests, o con otra
        # implementación) en vez de acoplar AuthService a la construcción
        # concreta de UserRepository. Si no se provee, se instancia a partir
        # de `db` para no romper el uso actual (AuthService(db) en
        # app/api/auth.py).
        self._repository = repository if repository is not None else UserRepository(db)

    def login(self, credentials: LoginRequest) -> LoginResponse:
        # Se loguea únicamente el email (dato no sensible) para trazabilidad;
        # la contraseña jamás se incluye en logs.
        logger.info("Intento de login para email=%s", credentials.email)

        user = self._repository.get_by_email(credentials.email)

        if user is None:
            logger.info("Login fallido (usuario inexistente) email=%s", credentials.email)
            raise _invalid_credentials_exception()

        if not verify_password(credentials.password, user.password_hash):
            logger.info("Login fallido (contraseña incorrecta) email=%s", credentials.email)
            raise _invalid_credentials_exception()

        access_token = create_access_token(subject=user.email)
        logger.info("Login exitoso email=%s", credentials.email)

        return LoginResponse(access_token=access_token, token_type="bearer")
