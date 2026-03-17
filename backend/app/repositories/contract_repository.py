# ============================================================
# REPOSITORIO DE CONTRATOS - contract_repository.py
# Capa de acceso a datos: todas las consultas SQL relacionadas
# con contratos pasan por aquí. Usa SQLAlchemy ORM para
# interactuar con PostgreSQL sin escribir SQL directamente.
# ============================================================

from sqlalchemy.orm import Session
from app.models.contract import Contrato

def get_contract_by_id(db: Session, contract_id: str):
    """
    Busca y retorna un contrato por su ID único (ej: 'CNT-2025-001').
    Retorna None si no existe.
    """
    return db.query(Contrato).filter(Contrato.id == contract_id).first()

def get_contracts(db: Session, skip: int = 0, limit: int = 100, user_id: int = None, es_biblioteca: bool = False, tipo: str = None):
    """
    Lista contratos con filtros opcionales.
    
    Parámetros:
    - skip / limit: paginación (cuántos saltar y cuántos traer)
    - user_id: si se provee, solo trae contratos del abogado con ese ID
    - es_biblioteca: False = contratos reales, True = cláusulas/plantillas
    - tipo: filtra por tipo específico ('clausula', 'plantilla', 'contrato')
    
    Siempre excluye registros con is_deleted=True (borrado lógico).
    """
    query = db.query(Contrato).filter(
        Contrato.es_biblioteca == es_biblioteca,
        Contrato.is_deleted == False  # Solo registros activos (no borrados)
    )
    if user_id:
        query = query.filter(Contrato.abogado_id == user_id)  # Filtrar por abogado
    if tipo:
        query = query.filter(Contrato.tipo == tipo)  # Filtrar por tipo
    return query.order_by(Contrato.id.desc()).offset(skip).limit(limit).all()

def create_contract(db: Session, db_contract: Contrato):
    """
    Inserta un nuevo contrato en la base de datos.
    db.add() → db.commit() → db.refresh() es el patrón estándar de SQLAlchemy.
    """
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)  # Recarga el objeto con los datos generados por la BD (ej: fechas)
    return db_contract

def update_contract(db: Session, db_contract: Contrato):
    """
    Guarda los cambios de un contrato existente.
    El objeto db_contract ya fue modificado por el servicio antes de llamar esto.
    """
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract

def delete_contract(db: Session, db_contract: Contrato):
    """
    BORRADO LÓGICO: marca el contrato como eliminado sin borrarlo físicamente.
    Esto preserva el historial y permite recuperación de datos si es necesario.
    is_deleted=True hace que el contrato no aparezca en ninguna consulta normal.
    """
    db_contract.is_deleted = True
    db.add(db_contract)
    db.commit()

def get_all_ids_by_prefix(db: Session, prefix: str):
    """
    Retorna todos los IDs de contratos que empiecen con el prefijo dado.
    Se usa para generar el próximo ID correlativo (ej: todos los 'CNT-2025-*').
    """
    return db.query(Contrato.id).filter(Contrato.id.like(f"{prefix}%")).all()

def count_contracts(db: Session, user_id: int = None, estado: str = None, es_biblioteca: bool = False):
    """
    Cuenta contratos según filtros. Se usa en el dashboard para mostrar estadísticas.
    La comparación de 'estado' es insensible a mayúsculas/minúsculas.
    """
    query = db.query(Contrato).filter(
        Contrato.es_biblioteca == es_biblioteca,
        Contrato.is_deleted == False
    )
    if user_id:
        query = query.filter(Contrato.abogado_id == user_id)
    if estado:
        from sqlalchemy import func
        query = query.filter(func.upper(Contrato.estado) == estado.upper())
    return query.count()
