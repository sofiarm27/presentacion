# ============================================================
# MODELO DE BASE DE DATOS - CONTRATOS - contract.py
# Define las tablas 'plantilla' y 'contrato'.
# Contrato es la tabla principal del sistema: almacena tanto
# contratos reales como elementos de biblioteca (cláusulas y
# plantillas) según el campo 'es_biblioteca'.
# ============================================================

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB   # Tipo JSON de PostgreSQL (permite consultas sobre el JSON)
from sqlalchemy.sql import func
from app.db.base_class import Base

class Plantilla(Base):
    """
    Tabla 'plantilla': almacena las plantillas de contratos predefinidas.
    Una plantilla puede ser la base para generar múltiples contratos.
    """
    __tablename__ = "plantilla"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)       # Nombre de la plantilla
    tipo = Column(String(50))                          # Tipo de servicio legal
    ultima_mod = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())  # Fecha de última modificación
    autor = Column(String(100))                        # Autor de la plantilla
    clause_ids = Column(JSONB)                         # IDs de cláusulas asociadas en formato JSON
    
    # Relación: una plantilla puede dar origen a muchos contratos
    contratos = relationship("Contrato", back_populates="plantilla")

class Contrato(Base):
    """
    Tabla 'contrato': tabla central del sistema.
    
    DOBLE USO según el campo 'es_biblioteca':
    - es_biblioteca=False: Contrato real asignado a un cliente y abogado
    - es_biblioteca=True:  Elemento de biblioteca (cláusula o plantilla reutilizable)
    
    El campo 'tipo' distingue entre: 'contrato', 'clausula', 'plantilla'
    El campo 'estado' puede ser: 'BORRADOR', 'ACTIVO', 'FIRMADO', etc.
    Las cláusulas del contrato se guardan como JSON en 'clauses'.
    El borrado es lógico: is_deleted=True oculta el registro sin eliminarlo.
    """
    __tablename__ = "contrato"
    id = Column(String(50), primary_key=True, index=True)         # ID con formato CNT-2025-001
    titulo = Column(String(255))                                   # Título descriptivo del contrato
    cliente_id = Column(Integer, ForeignKey("cliente.id"))         # Cliente asociado
    abogado_id = Column(Integer, ForeignKey("usuario.id"))         # Abogado responsable
    plantilla_id = Column(Integer, ForeignKey("plantilla.id"))     # Plantilla de origen (opcional)
    estado = Column(String(20), default="BORRADOR")                # Estado actual del contrato
    tipo = Column(String(50))                                      # Tipo: contrato, clausula, plantilla
    es_biblioteca = Column(Boolean, default=False)                 # True si es un elemento de biblioteca
    fecha = Column(Date, server_default=func.current_date())       # Fecha de creación/inicio
    total = Column(Numeric(15, 2))                                 # Valor económico total del contrato
    clauses = Column(JSONB)                                        # Cláusulas del contrato en formato JSON
    variables_adicionales = Column(JSONB)                         # Datos extra: modalidad de pago, cuotas, etc.
    is_deleted = Column(Boolean, default=False)                    # Borrado lógico (no se elimina físicamente)
    
    # Relaciones ORM para acceder a objetos relacionados desde Python
    cliente = relationship("Cliente", back_populates="contratos")
    abogado = relationship("Usuario", back_populates="contratos")
    plantilla = relationship("Plantilla", back_populates="contratos")
    pagos = relationship("Pago", back_populates="contrato")        # Cuotas/pagos asociados
