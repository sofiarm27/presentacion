# ============================================================
# CONFIGURACIÓN DE BASE DE DATOS - database.py
# Aquí se crea la conexión a PostgreSQL usando SQLAlchemy.
# get_db() se usa como dependencia en cada endpoint para
# obtener una sesión de base de datos y cerrarla al finalizar.
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import DATABASE_URL  # URL de conexión leída desde el .env

# Motor de conexión a PostgreSQL con timeout de 10 segundos
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 10})

# Fábrica de sesiones: cada solicitud al API obtiene su propia sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Generador que provee una sesión de base de datos por petición.
    Garantiza que la sesión siempre se cierre al terminar (bloque finally),
    aunque ocurra un error. Se usa con Depends(get_db) en los endpoints.
    """
    db = SessionLocal()
    try:
        yield db  # Cede la sesión al endpoint que la solicitó
    finally:
        db.close()  # Siempre cierra la conexión al finalizar la petición
