# --- Etapa 1: build de los assets estáticos (Vite) ---
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vacío por defecto: en producción el frontend llama a rutas relativas
# (/api/...) y nginx las reenvía al backend interno (ver nginx.conf).
# Solo hay que sobreescribirlo si el backend se sirve en otro dominio/host.
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# --- Etapa 2: servir con nginx ---
FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
