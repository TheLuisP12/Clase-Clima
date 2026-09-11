"""Router REST del dominio de consulta meteorológica."""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_email
from app.schemas.weather import WeatherResponse
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/api/v1", tags=["weather"])


@router.get(
    "/weather",
    response_model=WeatherResponse,
    status_code=200,
    summary="Consultar el clima actual de una ubicación",
)
def get_weather(
    location: str = Query(..., min_length=1, description="País o región a consultar"),
    _user_email: str = Depends(get_current_user_email),
) -> WeatherResponse:
    """Consulta el clima actual vía WeatherAPI para `location`.

    - 200: `{ location, temperature, condition, humidity }`.
    - 401: sin sesión activa (JWT ausente/inválido/expirado).
    - 404: la ubicación no existe para el proveedor externo.
    - 502: el proveedor externo no está disponible.
    """
    service = WeatherService()
    return service.get_weather(location)
