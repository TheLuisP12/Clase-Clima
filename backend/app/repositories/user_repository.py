"""Repositorio de acceso a datos para la entidad User.

Aísla al resto de la aplicación de los detalles de SQLAlchemy/consultas SQL.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_email(self, email: str) -> User | None:
        """Busca un usuario por email (comparación case-insensitive).

        El índice único sobre `email` (ver sql/001_create_users_table.sql)
        hace de esta consulta un lookup eficiente por índice.
        """
        normalized_email = email.strip().lower()
        stmt = select(User).where(func.lower(User.email) == normalized_email)
        return self._db.execute(stmt).scalar_one_or_none()

    def create(self, email: str, password_hash: str) -> User:
        user = User(email=email.strip().lower(), password_hash=password_hash)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
