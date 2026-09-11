"""Punto de entrada de la aplicación FastAPI."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("app")

try:
    settings = get_settings()
except Exception:
    # Falla rápido y con un log claro (nunca un 500 silencioso en runtime)
    # si la configuración es insegura, p.ej. JWT_SECRET por defecto en
    # ENVIRONMENT=production (ver validator en app.core.config.Settings).
    logger.error(
        "Configuración inválida al arrancar la aplicación: revisa "
        "JWT_SECRET/ENVIRONMENT. La app no puede levantar así."
    )
    raise

app = FastAPI(title="Proyecto 2 - Auth API", version="1.0.0")

# CORS: permite al front (Vite, dev en http://localhost:5173) consumir la API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.exception_handler(HTTPException)
async def known_http_exception_handler(request: Request, exc: HTTPException):
    """Re-expone las HTTPException controladas (401, 422, etc.) tal cual,
    delegando en el handler por defecto de FastAPI (no exponen stacktraces).
    """
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Red de seguridad para errores no controlados.

    Nunca se devuelve el stacktrace ni el detalle interno al cliente, y el
    log del servidor NO incluye el body de la request (que podría contener
    la contraseña en /api/auth/login).
    """
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
