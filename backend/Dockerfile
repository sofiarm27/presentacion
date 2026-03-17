FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para PostgreSQL y compilación
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación (asume que la carpeta backend/app se copia)
COPY ./ /app/

# Exponer el puerto (Railway inyecta $PORT, pero por convención ponemos 8000)
EXPOSE 8000

# Comando para ejecutar la aplicación. Usamos uvicorn.
# Nota: Railway pasa la variable de entorno $PORT dinámicamente.
# En Railway, es importante enlazar al host 0.0.0.0 y al puerto que Railway asigna.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
