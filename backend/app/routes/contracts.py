# ============================================================
# RUTAS DE CONTRATOS - routes/contracts.py
# Todos los endpoints del módulo de contratos.
# Incluye gestión de contratos reales, cláusulas y plantillas.
# Todos los endpoints requieren autenticación (JWT).
# ============================================================

from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user         # Dependencia de autenticación
from app.schemas.contract import ContratoSchema, ContratoCreate, ContratoUpdate, ClausulaCreate, ClausulaUpdate, PlantillaCreate, PlantillaUpdate, ContratoFromPlantilla
from app.repositories import contract_repository
from app.services import contract_service
from app.models.contract import Contrato

router = APIRouter()

# -------------------------------------------------------
# ENDPOINTS DE BIBLIOTECA LEGAL (Cláusulas y Plantillas)
# -------------------------------------------------------

@router.get("/clausulas", response_model=List[ContratoSchema])
def list_clausulas(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)  # Requiere token JWT válido
):
    """
    GET /contracts/clausulas
    Lista todas las cláusulas guardadas en la biblioteca legal.
    Filtra por: es_biblioteca=True y tipo='clausula'.
    """
    return contract_repository.get_contracts(db, es_biblioteca=True, tipo="clausula")

@router.get("/plantillas", response_model=List[ContratoSchema])
def list_plantillas(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    GET /contracts/plantillas
    Lista todas las plantillas de contratos en la biblioteca.
    Filtra por: es_biblioteca=True y tipo='plantilla'.
    """
    return contract_repository.get_contracts(db, es_biblioteca=True, tipo="plantilla")

@router.post("/clausula", response_model=ContratoSchema)
def create_clausula(
    clausula: ClausulaCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    POST /contracts/clausula
    Crea una nueva cláusula en la biblioteca legal.
    Genera ID con prefijo LIB y la marca como es_biblioteca=True.
    """
    return contract_service.create_library_item(db, clausula.model_dump(), "clausula")

@router.post("/plantilla", response_model=ContratoSchema)
def create_plantilla(
    plantilla: PlantillaCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    POST /contracts/plantilla
    Crea una nueva plantilla de contrato en la biblioteca.
    Genera ID con prefijo PLT y la marca como es_biblioteca=True.
    """
    return contract_service.create_library_item(db, plantilla.model_dump(), "plantilla")

@router.put("/clausula/{id}", response_model=ContratoSchema)
def update_clausula(
    id: str,
    clausula: ClausulaUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    PUT /contracts/clausula/{id}
    Actualiza una cláusula existente (titulo y/o texto).
    Retorna 404 si la cláusula no existe.
    """
    updated_item = contract_service.update_contract(db, id, clausula.model_dump(exclude_unset=True))
    if not updated_item:
        raise HTTPException(status_code=404, detail="Cláusula no encontrada")
    return updated_item

@router.put("/plantilla/{id}", response_model=ContratoSchema)
def update_plantilla(
    id: str,
    plantilla: PlantillaUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    PUT /contracts/plantilla/{id}
    Actualiza una plantilla existente. Permite actualización parcial.
    Retorna 404 si la plantilla no existe.
    """
    updated_item = contract_service.update_contract(db, id, plantilla.model_dump(exclude_unset=True))
    if not updated_item:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return updated_item

@router.delete("/clausula/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clausula(
    id: str,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    DELETE /contracts/clausula/{id}
    Elimina una cláusula de la biblioteca (borrado lógico: is_deleted=True).
    Retorna 204 No Content si exitoso, 404 si no existe.
    """
    item = db.query(Contrato).filter(Contrato.id == id, Contrato.es_biblioteca == True).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cláusula no encontrada")
    contract_repository.delete_contract(db, item)
    return None

@router.delete("/plantilla/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plantilla(
    id: str,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    DELETE /contracts/plantilla/{id}
    Elimina una plantilla de la biblioteca (borrado lógico).
    """
    item = db.query(Contrato).filter(Contrato.id == id, Contrato.es_biblioteca == True).first()
    if not item:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    contract_repository.delete_contract(db, item)
    return None

@router.post("/generar-desde-plantilla/{id}", response_model=ContratoSchema)
def generate_contract(
    id: str,
    contract_data: ContratoFromPlantilla,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    POST /contracts/generar-desde-plantilla/{id}
    Genera un contrato real a partir de una plantilla existente.
    Copia las cláusulas de la plantilla y asigna el cliente y abogado indicados.
    El contrato resultante tiene estado BORRADOR y es_biblioteca=False.
    """
    contract = contract_service.generate_contract_from_template(db, id, contract_data.model_dump())
    if not contract:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return contract

# -------------------------------------------------------
# ENDPOINTS DE CONTRATOS REALES
# -------------------------------------------------------

@router.get("/{id}", response_model=ContratoSchema)
def get_contract(
    id: str,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    GET /contracts/{id}
    Retorna los detalles de un contrato específico por su ID.
    Incluye los objetos anidados de cliente y abogado.
    """
    contract = contract_repository.get_contract_by_id(db, id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return contract

@router.put("/{id}", response_model=ContratoSchema)
def update_contract(
    id: str,
    contract: ContratoUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    PUT /contracts/{id}
    Actualiza un contrato existente. Permite actualización parcial
    (solo se actualizan los campos enviados en el body).
    También resincroniza los pagos si cambian los montos o cuotas.
    """
    updated_contract = contract_service.update_contract(db, id, contract.model_dump(exclude_unset=True))
    if not updated_contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return updated_contract

@router.post("/", response_model=ContratoSchema)
def create_contract(
    contract: ContratoCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    POST /contracts/
    Crea un nuevo contrato real.
    Genera el ID automáticamente (CNT-AÑO-NNN).
    Crea los registros de pago según la modalidad configurada.
    """
    return contract_service.create_contract(db=db, contract_data=contract.model_dump())

@router.get("/", response_model=List[ContratoSchema])
def read_contracts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    GET /contracts/
    Lista contratos con control de acceso por rol:
    - ADMINISTRADOR: ve todos los contratos del sistema
    - ABOGADO: solo ve sus propios contratos (donde es el abogado responsable)
    
    Soporta paginación con skip y limit.
    """
    # Verificar si el usuario tiene rol administrador
    is_admin = any(role.nombre.lower() == "administrador" for role in current_user.roles)
    # Si es admin: filter_user_id=None (sin filtro). Si es abogado: filtrar por su ID
    filter_user_id = None if is_admin else current_user.id
    return contract_repository.get_contracts(db, skip=skip, limit=limit, user_id=filter_user_id)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    id: str,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    DELETE /contracts/{id}
    Elimina un contrato (borrado lógico: is_deleted=True).
    El contrato desaparece de las consultas pero se preserva en BD.
    Retorna 204 No Content si exitoso, 404 si no existe.
    """
    contract = contract_repository.get_contract_by_id(db, id)
    if not contract:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    contract_repository.delete_contract(db, contract)
    return None
