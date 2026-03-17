FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos
COPY backend/requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación y scripts de utilidad
COPY backend/ /app/
COPY scripts/ /app/scripts/

# Comando para ejecutar la aplicación usando el puerto dinámico de Railway.
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
