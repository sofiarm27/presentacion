# ============================================================
# ESQUEMAS DE VALIDACIÓN - CONTRATOS - schemas/contract.py
# Define los modelos Pydantic que validan los datos de entrada
# y salida del API. Actúan como capa de validación automática
# antes de que los datos lleguen a la base de datos.
# ============================================================

from datetime import date
from typing import Optional, List, Any, Dict, Union
from decimal import Decimal
from pydantic import BaseModel
from .auth import UsuarioSchema     # Esquema anidado para incluir datos del abogado
from .client import ClienteSchema   # Esquema anidado para incluir datos del cliente

class ContratoBase(BaseModel):
    """
    Campos base compartidos entre creación, actualización y lectura de contratos.
    Todos los campos son opcionales para permitir actualizaciones parciales.
    """
    id: Optional[str] = None                          # ID con formato CNT-2025-001
    titulo: Optional[str] = None                      # Título del contrato
    cliente_id: Optional[int] = None                  # ID del cliente asociado
    abogado_id: Optional[int] = None                  # ID del abogado responsable
    plantilla_id: Optional[int] = None                # ID de la plantilla usada (opcional)
    estado: Optional[str] = "BORRADOR"                # Estado inicial por defecto
    tipo: Optional[str] = None                        # Tipo de contrato o servicio
    total: Optional[Decimal] = None                   # Valor económico total
    clauses: Optional[Union[Dict[str, Any], List[Any]]] = None  # Cláusulas en formato JSON
    variables_adicionales: Optional[Dict[str, Any]] = None       # Datos adicionales (cuotas, etc.)
    es_biblioteca: Optional[bool] = False             # True si es cláusula o plantilla de biblioteca

class ContratoCreate(ContratoBase):
    """
    Esquema para CREAR un contrato.
    Exige cliente_id y abogado_id (son obligatorios al crear).
    """
    cliente_id: int   # Obligatorio al crear
    abogado_id: int   # Obligatorio al crear

class ContratoUpdate(BaseModel):
    """
    Esquema para ACTUALIZAR un contrato existente.
    Todos los campos son opcionales (actualización parcial).
    Solo se actualizan los campos que se envíen.
    """
    titulo: Optional[str] = None
    cliente_id: Optional[int] = None
    abogado_id: Optional[int] = None
    plantilla_id: Optional[int] = None
    estado: Optional[str] = None
    tipo: Optional[str] = None
    total: Optional[Decimal] = None
    clauses: Optional[Union[Dict[str, Any], List[Any]]] = None
    variables_adicionales: Optional[Dict[str, Any]] = None
    fecha: Optional[date] = None

class ContratoSchema(ContratoBase):
    """
    Esquema de RESPUESTA: lo que el API devuelve al cliente.
    Incluye datos anidados del cliente y del abogado para
    no tener que hacer peticiones adicionales.
    """
    fecha: Optional[date] = None
    es_biblioteca: bool
    cliente: Optional[ClienteSchema] = None   # Objeto completo del cliente
    abogado: Optional[UsuarioSchema] = None   # Objeto completo del abogado
    class Config:
        from_attributes = True  # Permite convertir objetos SQLAlchemy a Pydantic

# -------------------------------------------------------
# ESQUEMAS PARA BIBLIOTECA LEGAL (Cláusulas y Plantillas)
# -------------------------------------------------------

class ClausulaCreate(BaseModel):
    """Datos requeridos para crear una cláusula en la biblioteca legal."""
    titulo: str   # Título descriptivo de la cláusula
    texto: str    # Contenido legal de la cláusula

class ClausulaUpdate(BaseModel):
    """Permite actualizar solo el título, solo el texto, o ambos."""
    titulo: Optional[str] = None
    texto: Optional[str] = None

class PlantillaCreate(BaseModel):
    """
    Datos para crear una plantilla en la biblioteca.
    Una plantilla contiene una lista de cláusulas predefinidas.
    """
    titulo: str
    tipo: Optional[str] = "Insolvencia Económica"  # Área de práctica legal
    descripcion: Optional[str] = None
    clauses: List[Dict[str, Any]]  # Lista de cláusulas: [{"titulo": "...", "texto": "...", "variables": [...]}]

class PlantillaUpdate(BaseModel):
    """Permitir actualización parcial de una plantilla."""
    titulo: Optional[str] = None
    tipo: Optional[str] = None
    descripcion: Optional[str] = None
    clauses: Optional[List[Dict[str, Any]]] = None

class ContratoFromPlantilla(BaseModel):
    """
    Datos necesarios para generar un contrato real a partir de una plantilla.
    El sistema copia las cláusulas de la plantilla y crea un contrato nuevo.
    """
    cliente_id: int                                   # Cliente para quien se genera el contrato
    abogado_id: int                                   # Abogado responsable del contrato
    total: Optional[Decimal] = None                   # Valor económico del contrato
    variables_adicionales: Optional[Dict[str, Any]] = None  # Variables a rellenar en las cláusulas
