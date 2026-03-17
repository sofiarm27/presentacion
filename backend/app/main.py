# ============================================================
# ARCHIVO PRINCIPAL DE LA APLICACIÓN - main.py
# Aquí se crea y configura la aplicación FastAPI.
# Es el punto de entrada del servidor backend.
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.base_class import Base  # Clase base para todos los modelos de SQLAlchemy
from app.core.database import engine  # Motor de conexión a PostgreSQL
from app.routes import auth, clients, contracts, users, stats, roles  # Importación de todos los routers

# Importamos los modelos para que SQLAlchemy los conozca al crear las tablas
print("Sincronizando modelos con la base de datos...")
from app.models import auth as auth_models, client, contract, payment
# Crea las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

# Auto-seeding del admin (opcional: podrías mover esto a una tarea o comando aparte)
try:
    from scripts.seed_admin import seed_admin
    print("Ejecutando seed de administrador...")
    seed_admin()
except ImportError:
    # Si no se encuentra el script en el path, intentamos importarlo de otra forma
    # o simplemente ignoramos si estamos en un entorno donde no debe ejecutarse
    print("Aviso: No se pudo ejecutar el seed automático del admin.")
except Exception as e:
    print(f"Error en seed automático: {e}")

# Creación de la instancia principal de FastAPI
app = FastAPI(title="LexContract API", version="1.0.0")

# -------------------------------------------------------
# CONFIGURACIÓN DE CORS (Cross-Origin Resource Sharing)
# Permite que el frontend (React en localhost:5173) pueda
# comunicarse con el backend (FastAPI en localhost:8000).
# Sin esto, el navegador bloquearía las peticiones.
# -------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Permitir todos los dominios en producción (ajustar luego por seguridad)
    allow_credentials=True,   # Permite envío de cookies y headers de autenticación
    allow_headers=["*"],      # Permite todos los headers
    allow_methods=["*"],      # Permite todos los métodos HTTP
    expose_headers=["*"],
)

# Ruta raíz para verificar que el servidor está en línea
@app.get("/")
def read_root():
    return {"message": "LexContract API is running (Professional Architecture)"}

# -------------------------------------------------------
# REGISTRO DE ROUTERS (módulos de rutas)
# Cada router agrupa los endpoints de un módulo específico
# -------------------------------------------------------
app.include_router(auth.router, tags=["auth"])                              # Login, recuperar contraseña
app.include_router(users.router, prefix="/users", tags=["users"])          # Gestión de usuarios
app.include_router(clients.router, prefix="/clients", tags=["clients"])    # Gestión de clientes
app.include_router(contracts.router, prefix="/contracts", tags=["contracts"]) # Gestión de contratos
app.include_router(stats.router, prefix="/stats", tags=["stats"])          # Estadísticas del dashboard
app.include_router(roles.router, prefix="/roles", tags=["roles"])          # Gestión de roles

# Nota: auth.router no tiene prefijo porque /token y /forgot-password
# están en la raíz del API (sin prefijo /auth/)
