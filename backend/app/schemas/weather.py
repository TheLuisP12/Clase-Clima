"""DTOs del dominio de consulta meteorológica (specs/02-Consulta-clima.md)."""

from pydantic import BaseModel


class WeatherResponse(BaseModel):
    """Respuesta exitosa de GET /api/v1/weather, tal como la define la spec."""

    location: str
    temperature: str
    condition: str
    humidity: str
