"""Router REST del dominio de autenticación."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=200,
    summary="Iniciar sesión con correo y contraseña",
)
def login(credentials: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Autentica al usuario y retorna un JWT.

    - 200: credenciales válidas -> { access_token, token_type }.
    - 401: usuario inexistente o contraseña incorrecta (mensaje genérico).
    - 422: `email` con formato inválido o `password` vacío/ausente
      (generado automáticamente por la validación de Pydantic/FastAPI,
      sin exponer la contraseña recibida).
    """
    service = AuthService(db)
    return service.login(credentials)
