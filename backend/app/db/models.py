"""Modelos ORM (SQLAlchemy) del dominio de autenticación."""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    """Usuario registrado.

    La contraseña NUNCA se guarda en texto plano: solo se persiste su hash
    (ver app.core.security.hash_password), cumpliendo el requisito del spec.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # OJO: la unicidad del email NO se declara aquí como `unique=True` plano
    # (case-sensitive). Se aplica más abajo como índice único funcional sobre
    # lower(email), para que sea equivalente al de la migración SQL y a la
    # búsqueda case-insensitive de UserRepository.get_by_email.
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        # Deliberadamente NO incluye password_hash en la representación.
        return f"User(id={self.id!r}, email={self.email!r})"


# Índice único funcional sobre lower(email): equivalente al
# `ux_users_email_lower` de sql/001_create_users_table.sql. Con esto,
# `Base.metadata.create_all(...)` (usado por scripts/seed_user.py y por la
# suite de QA con SQLite en memoria) produce una restricción case-insensitive
# consistente con la migración SQL en Postgres, corrigiendo BACK-2 del
# QA_REPORT.md. Coherente con el lookup case-insensitive de
# UserRepository.get_by_email (usa func.lower(User.email) también).
Index("ux_users_email_lower", func.lower(User.email), unique=True)
