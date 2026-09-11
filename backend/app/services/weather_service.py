"""Integración con el proveedor externo WeatherAPI (specs/02-Consulta-clima.md).

Nunca se loguea ni se devuelve al cliente la WEATHER_API_KEY, ni el detalle
crudo de la respuesta del proveedor externo.
"""

import logging

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.weather import WeatherResponse

logger = logging.getLogger("app.weather")

LOCATION_NOT_FOUND_MESSAGE = "Location not found"
PROVIDER_UNAVAILABLE_MESSAGE = "Weather service is currently unavailable"


class WeatherService:
    def __init__(self) -> None:
        self._settings = get_settings()

    def _fetch_from_provider(self, location: str) -> tuple[dict, int]:
        """Llama a WeatherAPI (current.json). Aislado en su propio método
        para poder sustituirlo fácilmente en tests (sin red real)."""
        response = httpx.get(
            f"{self._settings.WEATHER_API_BASE_URL}/current.json",
            params={"key": self._settings.WEATHER_API_KEY, "q": location},
            timeout=10.0,
        )
        body = response.json() if response.content else {}
        return body, response.status_code

    def get_weather(self, location: str) -> WeatherResponse:
        try:
            body, status_code = self._fetch_from_provider(location)
        except httpx.RequestError:
            logger.exception("Fallo de red al llamar a WeatherAPI (location=%s)", location)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=PROVIDER_UNAVAILABLE_MESSAGE,
            ) from None

        if status_code == 400:
            # WeatherAPI usa 400 tanto para ubicación no encontrada como para
            # parámetros inválidos; desde la perspectiva del usuario ambos
            # casos significan "esa ubicación no existe".
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=LOCATION_NOT_FOUND_MESSAGE,
            )

        if status_code != 200:
            logger.error(
                "WeatherAPI respondió %s para location=%s (detalle no expuesto al cliente)",
                status_code,
                location,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=PROVIDER_UNAVAILABLE_MESSAGE,
            )

        try:
            current = body["current"]
            return WeatherResponse(
                location=body["location"]["name"],
                temperature=f"{current['temp_c']}°C",
                condition=current["condition"]["text"],
                humidity=f"{current['humidity']}%",
            )
        except (KeyError, TypeError):
            logger.exception("Respuesta de WeatherAPI con forma inesperada (location=%s)", location)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=PROVIDER_UNAVAILABLE_MESSAGE,
            ) from None
