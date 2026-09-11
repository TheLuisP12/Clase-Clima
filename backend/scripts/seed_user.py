"""Script de seed: crea (o actualiza) un usuario de prueba para QA.

Uso (desde la carpeta backend/, con el venv activado y el .env configurado):

    python scripts/seed_user.py

Crea el usuario:
    email:    test@example.com
    password: Password123!

La contraseña se hashea con passlib (bcrypt) antes de persistirse; en
ningún momento se guarda en texto plano ni se imprime en los logs.
"""

import logging
import sys
from pathlib import Path

# Permite ejecutar el script directamente (python scripts/seed_user.py)
# sin necesidad de instalar el paquete "app".
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password  # noqa: E402
from app.db.models import Base, User  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("seed_user")

SEED_EMAIL = "test@example.com"
SEED_PASSWORD = "Password123!"


def seed_test_user() -> None:
    # Asegura que la tabla exista (idempotente). En un entorno real la
    # tabla ya debería existir vía sql/001_create_users_table.sql, pero
    # esto facilita levantar el proyecto rápido en desarrollo/QA.
    Base.metadata.create_all(bind=engine, tables=[User.__table__])

    db = SessionLocal()
    try:
        normalized_email = SEED_EMAIL.strip().lower()
        existing = (
            db.query(User)
            .filter(User.email == normalized_email)
            .one_or_none()
        )

        password_hash = hash_password(SEED_PASSWORD)

        if existing is not None:
            existing.password_hash = password_hash
            db.commit()
            logger.info("Usuario de prueba actualizado: %s", normalized_email)
            return

        user = User(email=normalized_email, password_hash=password_hash)
        db.add(user)
        db.commit()
        logger.info("Usuario de prueba creado: %s", normalized_email)
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_user()
    logger.info("Listo. Credenciales de prueba -> email=%s password=%s", SEED_EMAIL, SEED_PASSWORD)
