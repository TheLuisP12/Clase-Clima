# Backend - Login (FastAPI + PostgreSQL)

API de autenticación (correo + contraseña) implementada según `specs/01-login.md`.

## Estructura

```
backend/
  app/
    main.py                  # App FastAPI, CORS, exception handlers
    api/auth.py               # Router REST: POST /api/auth/login
    schemas/auth.py           # DTOs (LoginRequest, LoginResponse)
    services/auth_service.py  # Lógica de negocio (login, mensaje genérico)
    repositories/user_repository.py  # Acceso a datos (SQLAlchemy)
    db/session.py             # Engine + SessionLocal
    db/models.py              # Modelo ORM User
    core/config.py            # Settings (.env)
    core/security.py          # Hash de contraseñas (bcrypt) y JWT
  sql/001_create_users_table.sql   # Migración de la tabla users
  scripts/seed_user.py             # Crea un usuario de prueba
  requirements.txt
  .env.example
```

## Puesta en marcha

### 1. Crear y activar un entorno virtual

```bash
cd backend
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac
```

Edita `.env` y ajusta `DATABASE_URL` con las credenciales de tu PostgreSQL local,
y `JWT_SECRET` con un valor propio (no uses el de ejemplo en producción).

### 4. Crear la base de datos y ejecutar la migración

Con PostgreSQL corriendo y una base de datos ya creada (por ejemplo `proyecto2`):

```bash
psql -U postgres -d proyecto2 -f sql/001_create_users_table.sql
```

(Si `proyecto2` no existe: `createdb -U postgres proyecto2` o `CREATE DATABASE proyecto2;` desde `psql`.)

### 5. Crear el usuario de prueba (para QA)

```bash
python scripts/seed_user.py
```

Esto crea (o actualiza) el usuario:

- email: `test@example.com`
- password: `Password123!`

### 6. Levantar el servidor

```bash
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`. El frontend (Vite, dev)
corre por defecto en `http://localhost:5173`, ya habilitado en CORS
(`CORS_ORIGINS` en `.env`).

## Endpoint

### `POST /api/auth/login`

**Request**

```json
{ "email": "test@example.com", "password": "Password123!" }
```

**200 OK** (credenciales válidas)

```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

**401 Unauthorized** (usuario inexistente o contraseña incorrecta — mismo mensaje en ambos casos)

```json
{ "detail": "Invalid email or password" }
```

**422 Unprocessable Entity** (correo con formato inválido, o `email`/`password` vacíos o ausentes)

Generado automáticamente por la validación de Pydantic/FastAPI.

**500 Internal Server Error** (error inesperado no controlado)

```json
{ "detail": "Internal server error" }
```

Sin stacktrace ni detalles internos; el detalle real solo queda en los logs del servidor.
