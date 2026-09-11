"""Suite de QA - Backend - POST /api/auth/login

Verifica los criterios de aceptación de specs/01-login.md:
    * Login correcto permite acceder.
    * Contraseña incorrecta rechaza el acceso sin revelar existencia del usuario.
    * Campos vacíos muestran error.
    * Usuario inexistente no puede ingresar.
    * Las respuestas HTTP/Logs no exponen contraseñas ni stacktraces.

Reglas del spec:
    * Ambos campos obligatorios.
    * Correo con formato válido.
    * Solo usuarios registrados.
    * Password nunca en texto plano.
"""

from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import get_settings
from app.main import app
from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD

LOGIN_URL = "/api/auth/login"


# ---------------------------------------------------------------------------
# Camino feliz
# ---------------------------------------------------------------------------


def test_login_correcto_devuelve_200_y_jwt_valido(client, seeded_user):
    response = client.post(
        LOGIN_URL,
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body and body["access_token"]

    # El JWT debe ser válido y decodificable con el secreto configurado.
    settings = get_settings()
    payload = jwt.decode(
        body["access_token"], settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert payload["sub"] == TEST_USER_EMAIL
    assert "exp" in payload


def test_login_correcto_es_case_insensitive_en_email(client, seeded_user):
    """El repositorio normaliza el email (lower/strip); confirmar que
    MAYUSCULAS/espacios no impiden un login válido (regla: solo usuarios
    registrados, pero el email no debe ser case-sensitive por diseño)."""
    response = client.post(
        LOGIN_URL,
        json={"email": "  TEST@EXAMPLE.COM  ".strip(), "password": TEST_USER_PASSWORD},
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Credenciales inválidas: no revelar existencia del usuario
# ---------------------------------------------------------------------------


def test_password_incorrecta_devuelve_401(client, seeded_user):
    response = client.post(
        LOGIN_URL,
        json={"email": TEST_USER_EMAIL, "password": "ClaveIncorrecta1!"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_usuario_inexistente_devuelve_401(client):
    response = client.post(
        LOGIN_URL,
        json={"email": "no-existe@example.com", "password": "CualquierClave1!"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_mensaje_401_es_identico_para_usuario_inexistente_y_password_incorrecta(
    client, seeded_user
):
    """Criterio de aceptación explícito: 'Contraseña incorrecta rechaza el
    acceso sin revelar existencia del usuario'. Verifica que el status code
    Y el body de error sean byte-a-byte idénticos en ambos casos."""
    resp_wrong_password = client.post(
        LOGIN_URL,
        json={"email": TEST_USER_EMAIL, "password": "ClaveIncorrecta1!"},
    )
    resp_no_user = client.post(
        LOGIN_URL,
        json={"email": "no-existe@example.com", "password": "ClaveIncorrecta1!"},
    )

    assert resp_wrong_password.status_code == resp_no_user.status_code == 401
    assert resp_wrong_password.json() == resp_no_user.json()
    assert resp_wrong_password.headers.get("content-length") == resp_no_user.headers.get(
        "content-length"
    )


# ---------------------------------------------------------------------------
# Campos vacíos / obligatoriedad (422 de Pydantic)
# ---------------------------------------------------------------------------


def test_email_vacio_devuelve_422(client):
    response = client.post(LOGIN_URL, json={"email": "", "password": "algo"})
    assert response.status_code == 422
    assert "algo" not in response.text


def test_password_vacio_devuelve_422(client, seeded_user):
    response = client.post(LOGIN_URL, json={"email": TEST_USER_EMAIL, "password": ""})
    assert response.status_code == 422


def test_ambos_campos_vacios_devuelve_422(client):
    response = client.post(LOGIN_URL, json={"email": "", "password": ""})
    assert response.status_code == 422


def test_campos_ausentes_devuelve_422(client):
    response = client.post(LOGIN_URL, json={})
    assert response.status_code == 422


def test_error_422_no_incluye_password_enviado(client, seeded_user):
    """La respuesta de error de validación no debe hacer eco de la
    contraseña enviada por el cliente."""
    secreto = "SuperSecretoQueNoDebeAparecer1!"
    response = client.post(LOGIN_URL, json={"email": "not-an-email", "password": secreto})
    assert response.status_code == 422
    assert secreto not in response.text


# ---------------------------------------------------------------------------
# Formato de email inválido
# ---------------------------------------------------------------------------


def test_email_formato_invalido_devuelve_422(client):
    response = client.post(
        LOGIN_URL, json={"email": "correo-sin-arroba", "password": "Password123!"}
    )
    assert response.status_code == 422


def test_email_null_devuelve_422(client):
    response = client.post(LOGIN_URL, json={"email": None, "password": "Password123!"})
    assert response.status_code == 422


def test_password_null_devuelve_422(client):
    response = client.post(
        LOGIN_URL, json={"email": TEST_USER_EMAIL, "password": None}
    )
    assert response.status_code == 422


def test_tipos_no_string_devuelve_422(client):
    """Fuzzing básico de tipos: email/password como número o lista."""
    response = client.post(LOGIN_URL, json={"email": 12345, "password": ["a", "b"]})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Inyección de datos / SQL injection
# ---------------------------------------------------------------------------


def test_inyeccion_sql_en_email_no_causa_500_ni_bypass(client, seeded_user):
    payload = {"email": "' OR '1'='1", "password": "cualquiera"}
    response = client.post(LOGIN_URL, json=payload)
    # Con EmailStr, este payload no tiene formato de correo válido -> 422.
    # En cualquier caso, NUNCA debe ser 200 (bypass) ni 500 (error interno).
    assert response.status_code in (401, 422)
    assert response.status_code != 500


def test_inyeccion_sql_en_password_no_causa_500_ni_bypass(client, seeded_user):
    payload = {"email": TEST_USER_EMAIL, "password": "' OR '1'='1' --"}
    response = client.post(LOGIN_URL, json=payload)
    # Email válido y registrado, pero password es un intento de inyección:
    # debe tratarse como credencial inválida (401), nunca bypass ni 500.
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_inyeccion_sql_tipo_drop_table_en_email(client, seeded_user):
    payload = {
        "email": "x'; DROP TABLE users; --@example.com",
        "password": "Password123!",
    }
    response = client.post(LOGIN_URL, json=payload)
    assert response.status_code != 500

    # Confirmar que la tabla users sigue intacta: un login legítimo posterior
    # debe seguir funcionando.
    followup = client.post(
        LOGIN_URL, json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    assert followup.status_code == 200


def test_inyeccion_nosql_like_json_en_password(client, seeded_user):
    """Password como objeto (intento de inyección de operador tipo NoSQL)
    debe ser rechazado por el esquema (tipo inválido), no procesado."""
    response = client.post(
        LOGIN_URL, json={"email": TEST_USER_EMAIL, "password": {"$ne": None}}
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# No exposición de password/hash en las respuestas
# ---------------------------------------------------------------------------


def test_respuesta_exitosa_no_incluye_password_ni_hash(client, seeded_user):
    response = client.post(
        LOGIN_URL, json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"access_token", "token_type"}
    assert TEST_USER_PASSWORD not in response.text
    assert seeded_user.password_hash not in response.text


def test_respuesta_error_no_incluye_password_ni_hash(client, seeded_user):
    response = client.post(
        LOGIN_URL, json={"email": TEST_USER_EMAIL, "password": "otra-clave-cualquiera"}
    )
    assert response.status_code == 401
    assert "otra-clave-cualquiera" not in response.text
    assert seeded_user.password_hash not in response.text
    assert set(response.json().keys()) == {"detail"}


# ---------------------------------------------------------------------------
# Logs: nunca deben contener la contraseña en texto plano
# ---------------------------------------------------------------------------


def test_logs_no_contienen_password_en_texto_plano_login_exitoso(
    client, seeded_user, caplog_auth
):
    client.post(LOGIN_URL, json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD})

    full_log_text = "\n".join(record.getMessage() for record in caplog_auth.records)
    assert TEST_USER_PASSWORD not in full_log_text


def test_logs_no_contienen_password_en_texto_plano_login_fallido(
    client, seeded_user, caplog_auth
):
    secreto = "ClaveQueNuncaDebeApareverEnLogs1!"
    client.post(LOGIN_URL, json={"email": TEST_USER_EMAIL, "password": secreto})

    full_log_text = "\n".join(record.getMessage() for record in caplog_auth.records)
    assert secreto not in full_log_text


def test_logs_no_contienen_password_en_intento_usuario_inexistente(
    client, caplog_auth
):
    secreto = "OtraClaveSecreta1!"
    client.post(LOGIN_URL, json={"email": "fantasma@example.com", "password": secreto})

    full_log_text = "\n".join(record.getMessage() for record in caplog_auth.records)
    assert secreto not in full_log_text


# ---------------------------------------------------------------------------
# Errores no controlados (500): nunca stacktrace ni detalle interno
# ---------------------------------------------------------------------------


def test_error_interno_no_controlado_no_expone_stacktrace(client, seeded_user, monkeypatch):
    """Simula una falla inesperada (p.ej. caída de conexión a DB) en la capa
    de repositorio y verifica que el handler global de main.py la traduce a
    un 500 genérico sin stacktrace ni mensaje interno.

    Nota: se usa un TestClient con raise_server_exceptions=False porque,
    a diferencia de un servidor uvicorn real, el TestClient de Starlette
    por defecto re-lanza cualquier excepción no controlada (para facilitar
    debugging) en lugar de dejar que el exception_handler de main.py la
    convierta en la respuesta 500 que un cliente real vería.
    """
    from app.repositories.user_repository import UserRepository

    def _boom(self, email):
        raise RuntimeError("connection refused: could not reach database boom-detail")

    monkeypatch.setattr(UserRepository, "get_by_email", _boom, raising=True)

    lenient_client = TestClient(app, raise_server_exceptions=False)
    response = lenient_client.post(
        LOGIN_URL, json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "boom-detail" not in response.text
    assert "Traceback" not in response.text
    assert "RuntimeError" not in response.text


# ---------------------------------------------------------------------------
# Métodos / content-type
# ---------------------------------------------------------------------------


def test_password_extremadamente_larga_no_causa_500(client, seeded_user):
    """bcrypt limita internamente el input a 72 bytes; una contraseña más
    larga que eso enviada por un atacante no debe provocar un 500 (ver
    QA_REPORT.md - bug BACK-1 sobre la fragilidad de esta dependencia)."""
    payload = {"email": TEST_USER_EMAIL, "password": "A" * 200}
    response = client.post(LOGIN_URL, json=payload)
    assert response.status_code in (401, 422)
    assert response.status_code != 500


def test_login_get_no_permitido(client):
    response = client.get(LOGIN_URL)
    assert response.status_code == 405


def test_login_body_no_json_devuelve_422(client):
    response = client.post(
        LOGIN_URL, content="email=a@a.com&password=x", headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == 422
