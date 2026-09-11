"""DTOs (Pydantic) del flujo de autenticación."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Cuerpo esperado en POST /api/auth/login.

    - `email`: debe tener formato de correo válido (EmailStr lo valida y
      FastAPI responde 422 automáticamente si no cumple).
    - `password`: obligatoria y no vacía (min_length=1).
    """

    email: EmailStr
    password: str = Field(min_length=1, description="Contraseña en texto plano (solo en tránsito, nunca se persiste así).")


class LoginResponse(BaseModel):
    """Respuesta exitosa (HTTP 200) con el JWT de sesión."""

    access_token: str
    token_type: str = "bearer"
