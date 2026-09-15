#!/usr/bin/env bash
# Bootstrap de una instancia EC2 nueva (Amazon Linux 2023) para este proyecto.
#
# Se ejecuta UNA SOLA VEZ, a mano, por SSH, en la instancia recién creada:
#
#   curl -fsSL https://raw.githubusercontent.com/TheLuisP12/Clase-Clima/main/deploy/setup-ec2.sh -o setup-ec2.sh
#   bash setup-ec2.sh
#
# Después de correrlo, el despliegue automático vía GitHub Actions
# (.github/workflows/Gemini-ci-Vivecoding.yml) ya puede hacer
# "git pull && docker compose up -d --build" en cada push a main.
set -euo pipefail

REPO_URL="https://github.com/TheLuisP12/Clase-Clima.git"
APP_DIR="/home/ec2-user/app"

echo "==> Actualizando paquetes del sistema"
sudo dnf update -y

echo "==> Instalando Docker y git"
sudo dnf install -y docker git

echo "==> Habilitando e iniciando el servicio de Docker"
sudo systemctl enable docker
sudo systemctl start docker

echo "==> Agregando ec2-user al grupo docker (para usar docker sin sudo)"
sudo usermod -aG docker ec2-user

echo "==> Instalando el plugin de Docker Compose"
DOCKER_CONFIG="${DOCKER_CONFIG:-/usr/libexec/docker}"
sudo mkdir -p "$DOCKER_CONFIG/cli-plugins"
COMPOSE_VERSION="v2.29.7"
sudo curl -fsSL \
  "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
  -o "$DOCKER_CONFIG/cli-plugins/docker-compose"
sudo chmod +x "$DOCKER_CONFIG/cli-plugins/docker-compose"

echo "==> Clonando el repositorio en ${APP_DIR}"
if [ -d "$APP_DIR/.git" ]; then
  echo "    Ya existe, se omite el clone."
else
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

echo "==> Creando archivos .env a partir de las plantillas (si no existen)"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    Creado ./.env — EDÍTALO antes de levantar los contenedores."
fi
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  # Genera un JWT_SECRET aleatorio automáticamente.
  JWT_SECRET_VALUE=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))" 2>/dev/null || openssl rand -base64 48)
  sed -i "s|^JWT_SECRET=.*|JWT_SECRET=${JWT_SECRET_VALUE}|" backend/.env
  echo "    Creado ./backend/.env con un JWT_SECRET generado — EDÍTALO para poner WEATHER_API_KEY y demás."
fi

cat <<'EOF'

==> Bootstrap completo. Pasos pendientes (manuales):

1. Cierra esta sesión SSH y vuelve a conectarte (para que el grupo "docker" tome efecto):
     exit
     ssh ...

2. Edita los secretos reales antes del primer arranque:
     nano /home/ec2-user/app/.env
     nano /home/ec2-user/app/backend/.env
   (como mínimo: POSTGRES_PASSWORD, WEATHER_API_KEY)

3. Primer levantamiento manual (para validar que todo funciona):
     cd /home/ec2-user/app
     docker compose up -d --build

4. Verifica que el Security Group de la instancia permite entrada
   por el puerto 22 (SSH, para GitHub Actions) y por el puerto 80 (HTTP).

5. Configura en GitHub estos secrets (Settings > Secrets and variables > Actions):
     EC2_HOST     = IP pública de esta instancia
     EC2_USER     = ec2-user
     EC2_SSH_KEY  = contenido completo del .pem usado para conectarte

A partir de ahí, cada push a main en GitHub desplegará solo.
EOF
