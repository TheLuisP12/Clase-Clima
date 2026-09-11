"""Fixtures compartidas para la suite de QA del login (spec: specs/01-login.md).

Estrategia de aislamiento de datos:
    En vez de mockear el repositorio, se reemplaza la dependencia `get_db`
    de FastAPI (`app.db.session.get_db`) por una sesión de SQLAlchemy
    apuntando a una base SQLite en memoria. Esto permite ejercitar el
    código REAL de `AuthService` y `UserRepository` (sin tocar
    backend/app/**) sin depender de una instancia de PostgreSQL corriendo.

    SQLite en memoria requiere `StaticPool` + `check_same_thread=False`
    para que todas las conexiones del test compartan la misma DB.
"""

import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.models import Base, User
from app.db.session import get_db
from app.main import app

TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "Password123!"


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session_factory(db_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture()
def client(db_session_factory):
    """TestClient con la dependencia get_db sobreescrita a SQLite en memoria.

    No se modifica backend/app/**: solo se usa el mecanismo estándar de
    FastAPI `app.dependency_overrides`, pensado exactamente para testing.
    """

    def _override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded_user(db_session_factory):
    """Crea un usuario registrado con password hasheada (bcrypt real)."""
    db = db_session_factory()
    try:
        user = User(
            email=TEST_USER_EMAIL,
            password_hash=hash_password(TEST_USER_PASSWORD),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture()
def caplog_auth(caplog):
    """Captura logs del logger de autenticación en nivel INFO+."""
    caplog.set_level(logging.INFO, logger="app.auth")
    return caplog
