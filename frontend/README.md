# Frontend - Login

Proyecto Svelte + Vite + Tailwind CSS que implementa la pantalla de login según `specs/01-login.md`.

## Requisitos

- Node.js 18+ y npm.

## Configuración

1. Copia el archivo de variables de entorno de ejemplo:

   ```bash
   cp .env.example .env
   ```

2. Ajusta `VITE_API_URL` en `.env` si el backend no corre en `http://localhost:8000`.

## Instalación

```bash
npm install
```

## Desarrollo

```bash
npm run dev
```

La app quedará disponible en `http://localhost:5173`.

## Build de producción

```bash
npm run build
npm run preview
```

## Estructura relevante

- `src/lib/LoginForm.svelte`: formulario de login con validación reactiva del lado del cliente y consumo del endpoint `POST {VITE_API_URL}/api/auth/login`.
- `src/lib/Dashboard.svelte`: vista placeholder que se muestra tras un login exitoso.
- `src/App.svelte`: controla el cambio entre la vista de login y el dashboard.
