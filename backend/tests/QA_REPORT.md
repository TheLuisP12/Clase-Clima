# QA Report — Spec 01: Login

Autor: Quincy (QA). Alcance: `specs/01-login.md`. Código auditado (solo lectura):
`backend/app/**`, `frontend/src/**`. Suites de prueba creadas (no se tocó
código de producción): `backend/tests/`, `frontend/tests/`.

## 1. Entorno de ejecución

- Backend: Python 3.12.3, `pytest 9.1.1`, `httpx 0.28.1` + `fastapi.testclient.TestClient`.
  DB de prueba: **SQLite en memoria**, inyectada vía `app.dependency_overrides[get_db]`
  (mecanismo estándar de FastAPI). No se requirió PostgreSQL real ni se tocó
  `backend/app/**`.
- Frontend: Node 20.14.0, `vitest 2.1.9` + `@testing-library/svelte 4.x` + `jsdom`.
  `fetch` mockeado con `vi.stubGlobal`/`vi.fn`.
- **Ambas suites se ejecutaron realmente en este entorno** (no es una
  proyección): backend 27/27 tests OK, frontend 15/15 tests OK.

## 2. Resultado de ejecución

```
backend:  27 passed in ~6s   (python -m pytest, desde backend/)
frontend: 15 passed in ~7s   (npx vitest run, desde frontend/)
```

Archivos de test creados:
- `backend/tests/conftest.py`, `backend/tests/test_login.py`, `backend/pytest.ini`,
  `backend/tests/requirements-test.txt` (deps *solo* para correr los tests).
- `frontend/tests/setup.js`, `frontend/tests/LoginForm.test.js`,
  `frontend/vitest.config.js` (config de test separada de `vite.config.js`).
  Se agregaron devDependencies a `frontend/package.json`
  (`vitest`, `@testing-library/svelte`, `@testing-library/jest-dom`,
  `@testing-library/user-event`, `jsdom`) y scripts `test` / `test:watch`.

## 3. Criterios de aceptación (specs/01-login.md §6)

| # | Criterio | Estado | Evidencia |
|---|---|---|---|
| 1 | Login correcto permite acceder | **CUMPLIDO (con salvedad, ver BACK-1)** | `test_login_correcto_devuelve_200_y_jwt_valido`, `test_login_correcto_es_case_insensitive_en_email` (back); `LoginForm - login correcto (200)` (front, 3 tests). La lógica es correcta, pero ver bug **BACK-1**: con una instalación *limpia* de `backend/requirements.txt` (sin fijar `bcrypt`), este flujo falla con 500 para TODO intento de login, correcto o no. |
| 2 | Contraseña incorrecta rechaza el acceso sin revelar existencia del usuario | **CUMPLIDO** | `test_mensaje_401_es_identico_para_usuario_inexistente_y_password_incorrecta` (compara status + body byte-a-byte); frontend nunca lee el `body` del error (`LoginForm.svelte` líneas 63-78) y muestra el mismo texto fijo en ambos casos (`test: "muestra EXACTAMENTE el mismo mensaje genérico..."`). |
| 3 | Campos vacíos muestran error | **CUMPLIDO** | Backend: 422 automático de Pydantic (`test_email_vacio_devuelve_422`, `test_password_vacio_devuelve_422`, `test_ambos_campos_vacios_devuelve_422`, `test_campos_ausentes_devuelve_422`). Frontend: validación reactiva bloquea el submit y muestra mensaje sin llegar a hacer fetch (`test: "NO realiza ninguna petición de red con campos vacíos"`). |
| 4 | Usuario inexistente no puede ingresar | **CUMPLIDO** | `test_usuario_inexistente_devuelve_401`. |
| 5 | Las respuestas HTTP/Logs no exponen contraseñas ni stacktraces | **CUMPLIDO** | Respuestas: `test_respuesta_exitosa_no_incluye_password_ni_hash`, `test_respuesta_error_no_incluye_password_ni_hash`, `test_error_422_no_incluye_password_enviado`. Logs: `test_logs_no_contienen_password_en_texto_plano_*` (3 tests, via `caplog`). 500 sin stacktrace: `test_error_interno_no_controlado_no_expone_stacktrace` (confirma que `app/main.py` nunca filtra el detalle de una excepción real). |

Reglas del spec (§4): "ambos campos obligatorios", "correo formato válido",
"solo usuarios registrados", "password nunca en texto plano" → todas
verificadas y **CUMPLIDAS** por el código actual (`schemas/auth.py` usa
`EmailStr` + `min_length=1`; `db/models.py` solo persiste `password_hash`
vía bcrypt).

## 4. Bugs encontrados

### BACK-1 (CRÍTICO — Bastian) — `backend/requirements.txt` no fija una versión compatible de `bcrypt`; rompe el 100% de los logins en una instalación limpia

**Regla del spec que rompe:** "Login correcto permite acceder" (§6) y, de
forma indirecta, "la contraseña no se almacena en texto plano (requiere
hash)" (§4), porque el mecanismo de hash queda inutilizable.

**Repro (reproducido en este entorno):**
```
pip install passlib[bcrypt]==1.7.4   # exactamente lo fijado en requirements.txt
# => instala bcrypt 5.0.0 (no está pinneado, "passlib[bcrypt]" solo pide bcrypt>=3.1.0)
python -c "from app.core.security import hash_password; hash_password('Password123!')"
# => AttributeError: module 'bcrypt' has no attribute '__about__'
# => ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
```
`passlib==1.7.4` (2020) detecta la versión de `bcrypt` leyendo
`bcrypt.__about__.__version__`, atributo que `bcrypt>=4.1` eliminó. Esto
hace que la propia rutina de auto-detección de bugs de passlib falle
internamente, y `hash_password`/`verify_password` lanzan una excepción para
**cualquier** contraseña, incluso las cortas. Como `backend/requirements.txt`
no fija `bcrypt` explícitamente, un `pip install -r requirements.txt` hoy
instala la última versión de `bcrypt` y **deja el login (y el seed de
usuarios) completamente roto**, manifestándose como HTTP 500 en
`/api/auth/login` para toda combinación de credenciales.

**Para reproducir la suite de QA se tuvo que fijar manualmente
`bcrypt==4.0.1`** (ver `backend/tests/requirements-test.txt`, comentario al
inicio). Con ese pin, todos los tests pasan.

**Sugerencia para Bastian (no aplicada, QA no corrige código):** fijar en
`requirements.txt` una versión de `bcrypt` compatible con `passlib 1.7.4`
(p.ej. `bcrypt>=3.2,<4.1`, o `bcrypt==4.0.1`), o migrar a una versión de
`passlib`/librería de hashing con soporte activo para `bcrypt` 4.x/5.x.

**Severidad:** Crítica — bloquea el criterio de aceptación #1 en cualquier
entorno donde se instalen las dependencias "desde cero" (CI, onboarding de
un nuevo dev, deploy nuevo), sin que nada en el código de la app lo detecte
salvo el 500 genérico.

### BACK-2 (Menor / hallazgo de robustez — Bastian) — Índice único case-insensitive del email no se replica si se usa `Base.metadata.create_all`

`sql/001_create_users_table.sql` crea `UNIQUE INDEX ... ON users (lower(email))`,
pero el modelo SQLAlchemy (`app/db/models.py`) declara
`unique=True` sobre la columna `email` tal cual (sin `lower()`). El propio
`backend/scripts/seed_user.py` bootstrapea la tabla con
`Base.metadata.create_all(...)`, que solo aplicará el índice único
"case-sensitive" del modelo ORM, no el índice funcional de la migración SQL.
Hoy no es explotable porque no existe endpoint de registro, pero es una
inconsistencia de esquema que un futuro `POST /api/users` (registro)
heredaría silenciosamente si el entorno se levantó solo con `create_all`
(permitiría registrar `user@mail.com` y `User@mail.com` como cuentas
distintas, rompiendo la búsqueda case-insensitive que sí implementa
`UserRepository.get_by_email`). No bloquea el spec de Login actual.

### FRONT-1 (Observación, no bug — Fiona) — Nombre de la clave de `localStorage`

El componente guarda el JWT bajo la clave `'jwt'` (`localStorage.setItem('jwt', token)`,
`LoginForm.svelte` línea 68), leyendo el valor con fallback
`data?.token ?? data?.access_token ?? data?.jwt`. Es internamente
consistente (`App.svelte` también usa `'jwt'`) y el fallback sí resuelve
`access_token` correctamente, por lo que **no es un bug funcional**, solo se
documenta para que Fiona confirme que es la convención deseada del proyecto
(y no un resto de una iteración previa del contrato de la API).

## 5. Revisión de código (sin corregir)

- **`AuthService.__init__` instancia `UserRepository(db)` directamente**
  (`services/auth_service.py:32`) en vez de recibirlo inyectado. Acopla la
  capa de servicio a la implementación concreta del repositorio; dificulta
  testear `AuthService` en aislamiento total (esta suite lo evita
  reemplazando la sesión de DB completa, pero un mock de repositorio sería
  más simple/rápido). Sugerencia de diseño para Bastian, no bloqueante.
- **Duplicación menor en `LoginForm.svelte`**: `password = ''` se ejecuta
  tanto en la rama de éxito (línea 71) como en el bloque `finally` (línea
  85), volviendo el primero redundante. Inofensivo pero es limpieza
  pendiente para Fiona.
- **Función PL/pgSQL `find_user_by_email`** (`sql/001_create_users_table.sql`)
  está definida pero **no la invoca ningún código Python** (el repositorio
  usa el ORM de SQLAlchemy). No es un bug, pero es código muerto /
  mantenimiento duplicado (dos formas de hacer la misma búsqueda) — a
  evaluar si se elimina o se documenta su propósito real.
- **Secreto JWT por defecto inseguro**: `JWT_SECRET: str = "change-me-in-production"`
  (`core/config.py:17`) es un valor por defecto funcional pero
  intencionalmente inseguro; no hay chequeo que impida arrancar la app en
  producción con el valor por defecto sin cambiar. Fuera del alcance
  estricto del spec de Login, pero es una nota de hardening para Bastian.
- **Sin límite de intentos / rate limiting** en `/api/auth/login`: el spec
  no lo exige explícitamente, pero se deja como observación de seguridad
  (fuerza bruta) para una futura iteración.
- Nada de código duplicado relevante se encontró entre frontend y backend
  más allá de lo anotado arriba; la separación router → service →
  repository en el backend está razonablemente bien delegada, y el
  componente `LoginForm.svelte` mantiene la validación y el fetch en un
  único lugar cohesivo.

## 6. No verificable en este entorno

- No se probó contra una instancia real de **PostgreSQL** (se usó SQLite en
  memoria como sustituto funcionalmente equivalente para la lógica de
  negocio); el comportamiento específico de PL/pgSQL
  (`find_user_by_email`) y de la restricción `UNIQUE INDEX ... (lower(email))`
  de la migración SQL no se ejercitó directamente (ver BACK-2).
- No se ejecutó la app end-to-end con `uvicorn` + navegador real (CORS,
  timing real de red); las pruebas de frontend mockean `fetch` y las de
  backend usan `TestClient` en proceso.
