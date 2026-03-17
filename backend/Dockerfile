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

# Copiar el código de la aplicación
COPY backend/ /app/

# Exponer el puerto 8000 explícitamente
EXPOSE 8000

# Comando para ejecutar la aplicación. Usamos uvicorn en el puerto 8000 fijo.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
