# Imagen de producción del backend (FastAPI + Uvicorn).
FROM python:3.12-slim

WORKDIR /app

# psycopg2-binary trae sus propias libs precompiladas: no hacen falta
# paquetes de build de sistema.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
