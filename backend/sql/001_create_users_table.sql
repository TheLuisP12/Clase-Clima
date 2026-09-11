-- Migración 001: tabla de usuarios para el flujo de Login (specs/01-login.md)
--
-- Requisitos cubiertos:
--   * password_hash: la contraseña NUNCA se guarda en texto plano.
--   * email: único e indexado, para lookup eficiente y para impedir
--     usuarios duplicados.

BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice único sobre el email en minúsculas: evita duplicados como
-- "user@mail.com" vs "User@Mail.com" y acelera el lookup por email
-- (idéntico al usado por UserRepository.get_by_email).
CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email_lower
    ON users (lower(email));

COMMIT;
