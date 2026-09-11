"""Suite de QA - Backend - GET /api/v1/weather

Verifica los criterios de aceptación de specs/02-Consulta-clima.md:
    * Escenario 1: con sesión activa y ubicación válida, devuelve el clima.
    * Escenario 2: sin sesión activa, la acción se bloquea (401).
    * El proveedor externo (WeatherAPI) nunca expone su detalle crudo ni la
      API key al cliente, y sus fallos no provocan un 500.
"""

import httpx

from app.core.security import create_access_token
from app.services.weather_service import WeatherService
from tests.conftest import TEST_USER_EMAIL

WEATHER_URL = "/api/v1/weather"


def _auth_headers(subject: str = TEST_USER_EMAIL) -> dict:
    access_token = create_access_token(subject=subject)
    return {"Authorization": f"Bearer {access_token}"}


def _mock_provider_success(monkeypatch, *, location="Peru", temp_c=24, condition="Despejado", humidity=60):
    def _fake_fetch(self, requested_location):
        return (
            {
                "location": {"name": location},
                "current": {
                    "temp_c": temp_c,
                    "condition": {"text": condition},
                    "humidity": humidity,
                },
            },
            200,
        )

    monkeypatch.setattr(WeatherService, "_fetch_from_provider", _fake_fetch)


# ---------------------------------------------------------------------------
# Escenario 2: sin sesión activa
# ---------------------------------------------------------------------------


def test_sin_header_authorization_devuelve_401(client):
    response = client.get(WEATHER_URL, params={"location": "Peru"})
    assert response.status_code == 401


def test_token_invalido_devuelve_401(client):
    response = client.get(
        WEATHER_URL,
        params={"location": "Peru"},
        headers={"Authorization": "Bearer token-invalido"},
    )
    assert response.status_code == 401


def test_header_authorization_sin_scheme_bearer_devuelve_401(client):
    token = create_access_token(subject=TEST_USER_EMAIL)
    response = client.get(
        WEATHER_URL,
        params={"location": "Peru"},
        headers={"Authorization": token},
    )
    assert response.status_code == 401


def test_token_expirado_devuelve_401(client):
    expired_token = create_access_token(subject=TEST_USER_EMAIL, expires_minutes=-1)
    response = client.get(
        WEATHER_URL,
        params={"location": "Peru"},
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Escenario 1: consulta exitosa con sesión activa
# ---------------------------------------------------------------------------


def test_consulta_exitosa_devuelve_200_con_forma_esperada(client, monkeypatch):
    _mock_provider_success(monkeypatch, location="Peru", temp_c=24, condition="Despejado", humidity=60)

    response = client.get(WEATHER_URL, params={"location": "Peru"}, headers=_auth_headers())

    assert response.status_code == 200
    assert response.json() == {
        "location": "Peru",
        "temperature": "24°C",
        "condition": "Despejado",
        "humidity": "60%",
    }


def test_location_faltante_devuelve_422(client):
    response = client.get(WEATHER_URL, headers=_auth_headers())
    assert response.status_code == 422


def test_location_vacia_devuelve_422(client):
    response = client.get(WEATHER_URL, params={"location": ""}, headers=_auth_headers())
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Errores del proveedor externo: nunca 500, nunca se expone detalle interno
# ---------------------------------------------------------------------------


def test_ubicacion_no_encontrada_en_proveedor_devuelve_404(client, monkeypatch):
    def _fake_fetch(self, location):
        return {"error": {"code": 1006, "message": "No matching location found."}}, 400

    monkeypatch.setattr(WeatherService, "_fetch_from_provider", _fake_fetch)

    response = client.get(
        WEATHER_URL, params={"location": "Atlantida"}, headers=_auth_headers()
    )
    assert response.status_code == 404
    assert "1006" not in response.text


def test_fallo_de_red_al_proveedor_devuelve_502_no_500(client, monkeypatch):
    def _fake_fetch(self, location):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(WeatherService, "_fetch_from_provider", _fake_fetch)

    response = client.get(WEATHER_URL, params={"location": "Peru"}, headers=_auth_headers())
    assert response.status_code == 502
    assert "connection refused" not in response.text


def test_api_key_invalida_en_proveedor_no_expone_detalle(client, monkeypatch):
    def _fake_fetch(self, location):
        return {"error": {"code": 2006, "message": "API key provided is invalid"}}, 401

    monkeypatch.setattr(WeatherService, "_fetch_from_provider", _fake_fetch)

    response = client.get(WEATHER_URL, params={"location": "Peru"}, headers=_auth_headers())
    assert response.status_code == 502
    assert "API key" not in response.text


def test_respuesta_del_proveedor_con_forma_inesperada_no_causa_500(client, monkeypatch):
    def _fake_fetch(self, location):
        return {"algo": "inesperado"}, 200

    monkeypatch.setattr(WeatherService, "_fetch_from_provider", _fake_fetch)

    response = client.get(WEATHER_URL, params={"location": "Peru"}, headers=_auth_headers())
    assert response.status_code == 502


def test_inyeccion_en_location_no_causa_500(client, monkeypatch):
    _mock_provider_success(monkeypatch)
    response = client.get(
        WEATHER_URL,
        params={"location": "'; DROP TABLE users; --"},
        headers=_auth_headers(),
    )
    assert response.status_code != 500


def test_weather_api_key_nunca_se_expone_en_la_respuesta(client, monkeypatch):
    _mock_provider_success(monkeypatch)
    response = client.get(WEATHER_URL, params={"location": "Peru"}, headers=_auth_headers())

    from app.core.config import get_settings

    settings = get_settings()
    assert settings.WEATHER_API_KEY not in response.text
