"""Configuración centralizada de la aplicación.

Todas las variables sensibles (credenciales de BD, secreto JWT) se cargan
desde el entorno (.env en desarrollo) y NUNCA se hardcodean ni se loguean.
"""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valor por defecto de desarrollo para JWT_SECRET. Es funcional (permite
# levantar el proyecto localmente sin configuración extra) pero inseguro:
# nunca debe usarse en producción (ver validator más abajo).
_INSECURE_DEFAULT_JWT_SECRET = "change-me-in-production"


class Settings(BaseSettings):
    # --- Entorno ---
    # "development" (default) | "production". Se usa únicamente para el
    # chequeo de arranque de JWT_SECRET; sin sobrediseño de un concepto de
    # entorno más amplio.
    ENVIRONMENT: str = "development"

    # --- Base de datos ---
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/proyecto2"

    # --- JWT ---
    JWT_SECRET: str = _INSECURE_DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # --- CORS (front en desarrollo, Vite) ---
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def _validar_jwt_secret_en_produccion(self) -> "Settings":
        """Falla rápido al arrancar si en producción se sigue usando el
        JWT_SECRET por defecto (inseguro). En desarrollo no exige nada extra.
        """
        es_produccion = self.ENVIRONMENT.strip().lower() == "production"
        secreto_inseguro = self.JWT_SECRET == _INSECURE_DEFAULT_JWT_SECRET

        if es_produccion and secreto_inseguro:
            raise ValueError(
                "JWT_SECRET inseguro: se detectó el valor por defecto "
                f"'{_INSECURE_DEFAULT_JWT_SECRET}' con ENVIRONMENT=production. "
                "Configura un JWT_SECRET fuerte mediante variable de entorno "
                "(o .env) antes de levantar la aplicación en producción."
            )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Settings cacheadas (singleton) para evitar releer el entorno en cada request."""
    return Settings()
