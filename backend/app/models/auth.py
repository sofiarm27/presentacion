# ============================================================
# MODELOS DE BASE DE DATOS - AUTENTICACIÓN - auth.py
# Define las tablas 'usuario', 'rol' y la tabla intermedia
# 'usuario_rol' para la relación muchos a muchos (M:N).
# SQLAlchemy convierte estas clases en tablas de PostgreSQL.
# ============================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# -------------------------------------------------------
# TABLA DE ASOCIACIÓN: usuario_rol
# Permite que un usuario tenga múltiples roles y un rol
# sea asignado a múltiples usuarios (relación M:N).
# ondelete="CASCADE" borra los registros asociados si se
# elimina un usuario o un rol.
# -------------------------------------------------------
usuario_rol = Table(
    'usuario_rol', Base.metadata,
    Column('usuario_id', Integer, ForeignKey('usuario.id', ondelete="CASCADE"), primary_key=True),
    Column('rol_id', Integer, ForeignKey('rol.id', ondelete="CASCADE"), primary_key=True)
)

class Rol(Base):
    """
    Tabla 'rol': almacena los roles del sistema (ej: Administrador, Abogado).
    Relación M:N con Usuario a través de la tabla usuario_rol.
    """
    __tablename__ = "rol"
    id = Column(Integer, primary_key=True, index=True)          # ID autoincremental
    nombre = Column(String(50), unique=True, nullable=False)    # Nombre único del rol
    
    # Relación inversa: qué usuarios tienen este rol
    usuarios = relationship("Usuario", secondary=usuario_rol, back_populates="roles")

class Usuario(Base):
    """
    Tabla 'usuario': almacena todos los usuarios del sistema (abogados y administradores).
    Contiene información personal, credenciales y estado de la cuenta.
    """
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, index=True)              # ID autoincremental
    nombre = Column(String(100), nullable=False)                    # Nombre del usuario
    apellido = Column(String(100), nullable=False)                  # Apellido del usuario
    cedula = Column(String(20), unique=True, nullable=False)        # Documento de identidad (único)
    celular = Column(String(20), unique=True)                       # Número de teléfono (único)
    correo = Column(String(100), unique=True, index=True, nullable=False)  # Correo (usado para login)
    password = Column(String(255), nullable=False)                  # Contraseña cifrada con bcrypt
    estado = Column(String(20), default="Activo")                   # Activo / Inactivo / Bloqueado
    intentos_fallidos = Column(Integer, default=0)                  # Contador de intentos de login fallidos
    biografia = Column(Text)                                        # Descripción del perfil del abogado
    ultima_conexion = Column(DateTime(timezone=True))               # Última vez que inició sesión
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())  # Fecha de registro
    
    # Relaciones ORM
    roles = relationship("Rol", secondary=usuario_rol, back_populates="usuarios")  # Roles asignados
    contratos = relationship("Contrato", back_populates="abogado")                 # Contratos a cargo
