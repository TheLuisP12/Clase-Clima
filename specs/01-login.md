# SPEC: Login

## 1. Objetivo
Sistema de inicio de sesión mediante correo y contraseña.

## 2. Tecnologías y Stack (Obligatorio)
* **Frontend:** Svelte y Tailvind (componentes reactivos).
* **Backend:** Python (FastApi).
* **Base de Datos:** PostgreSQL (con PL/pgSQL si se requieren funciones).
* **Control de Versiones:** Git (commits en inglés con estándar `feat/fix`).

## 3. Requisitos
* Ingresar correo y contraseña.
* Validar los datos (formato y obligatoriedad).
* Mostrar mensaje de error si son incorrectos.
* Permitir acceso si son válidos y retornar JWT.

## 4. Reglas
* Ambos campos son obligatorios.
* El correo debe tener formato válido.
* Solo usuarios registrados pueden acceder.
* La contraseña no se almacena en texto plano (requiere hash).

## 5. Flujo
1. Usuario ingresa sus datos.
2. Fiona (Front) realiza validación reactiva de campos.
3. Se envía POST al backend.
4. Bastian (Back) verifica credenciales en PostgreSQL.
5. Si son correctas -> inicia sesión (HTTP 200).
6. Si son incorrectas -> muestra error genérico (HTTP 401).

## 6. Criterios de aceptación (Para Quincy)
* [ ] Login correcto permite acceder.
* [ ] Contraseña incorrecta rechaza el acceso sin revelar existencia del usuario.
* [ ] Campos vacíos muestran error.
* [ ] Usuario inexistente no puede ingresar.
* [ ] Las respuestas HTTP/Logs no exponen contraseñas ni stacktraces.
