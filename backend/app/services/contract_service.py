# ============================================================
# SERVICIO DE CONTRATOS - contract_service.py
# Capa de lógica de negocio: aquí está toda la lógica
# compleja del módulo de contratos. Los routes llaman a esta
# capa, y esta capa llama al repositorio para acceder a BD.
# ============================================================

from datetime import date
from sqlalchemy.orm import Session
from app.models.contract import Contrato
from app.models.payment import Pago
from app.repositories import contract_repository

def generate_id(db: Session, prefix_base: str):
    """
    Genera un ID único con formato: PREFIJO-AÑO-NNN
    Ejemplo: 'CNT-2025-001', 'PLT-2025-003', 'LIB-2025-012'
    
    Busca todos los IDs existentes con ese prefijo y año,
    determina el máximo número, y retorna el siguiente.
    Garantiza IDs correlativos y sin repetición.
    """
    year = date.today().year
    prefix = f"{prefix_base}-{year}-"
    existing_ids = contract_repository.get_all_ids_by_prefix(db, prefix)
    
    max_num = 0
    for (eid,) in existing_ids:
        try:
            num = int(eid.replace(prefix, ""))
            if num > max_num: max_num = num
        except ValueError: continue
    
    next_num = max_num + 1
    return f"{prefix}{str(next_num).zfill(3)}"  # zfill(3) agrega ceros: 001, 002, ...

def sync_payments(db: Session, db_contract: Contrato):
    """
    Sincroniza las cuotas de pago del contrato con la tabla 'pago'.
    
    Lee la modalidad de pago y las cuotas de 'variables_adicionales',
    borra los pagos anteriores del contrato y crea los nuevos.
    
    Modalidades:
    - 'unico': crea un solo registro de pago por el total
    - Cuotas (installments): crea un registro por cada cuota con su monto y fecha
    
    No hace nada si el contrato es un elemento de biblioteca (es_biblioteca=True).
    """
    if db_contract.es_biblioteca:
        return  # Las cláusulas y plantillas no tienen pagos asociados
    
    vars_adicionales = db_contract.variables_adicionales or {}
    modalidad = vars_adicionales.get("modalidadPago")        # 'unico' o 'cuotas'
    installments = vars_adicionales.get("installments", [])  # Lista de cuotas

    # Calcular el total automáticamente sumando las cuotas si no está definido
    contrato_total = db_contract.total or 0
    if not contrato_total and installments:
        try:
            contrato_total = sum(
                float(str(inst.get("monto", 0)).replace(",", ""))
                for inst in installments
            )
        except Exception:
            contrato_total = 0
    
    # Borrar pagos existentes para recrearlos (sincronización completa)
    db.query(Pago).filter(Pago.contrato_id == db_contract.id).delete()
    
    # PAGO ÚNICO: un solo pago por el monto total
    if (modalidad == "unico" or not installments) and contrato_total > 0:
        pago_unico = Pago(
            contrato_id=db_contract.id,
            tipo_pago="UNICO",
            monto_total_contrato=contrato_total,
            monto_abono=contrato_total,
            fecha_vencimiento=db_contract.fecha,
            estado="PENDIENTE"
        )
        db.add(pago_unico)
    elif installments:
        # PAGO EN CUOTAS: un registro de pago por cada cuota
        for inst in installments:
            monto = inst.get("monto", 0)
            if isinstance(monto, str):
                try:
                    monto = float(monto.replace(",", ""))  # Limpiar formato numérico
                except:
                    monto = 0
            
            pago = Pago(
                contrato_id=db_contract.id,
                tipo_pago="ABONO",
                monto_total_contrato=contrato_total,
                monto_abono=monto,
                fecha_vencimiento=inst.get("fecha") if inst.get("fecha") else None,
                estado="PENDIENTE"
            )
            db.add(pago)
    
    db.commit()  # Confirmar todos los cambios en la base de datos

def create_contract(db: Session, contract_data: dict):
    """
    Crea un contrato real (es_biblioteca=False).
    
    1. Genera el ID correlativo si no viene uno definido (CNT-2025-001)
    2. Convierte el estado a mayúsculas para consistencia
    3. Crea el objeto en la BD
    4. Sincroniza los pagos correspondientes
    """
    if not contract_data.get("id"):
        contract_data["id"] = generate_id(db, "CNT")  # Prefijo CNT para contratos
    if "estado" in contract_data:
        contract_data["estado"] = str(contract_data["estado"]).upper()
    db_contract = Contrato(**contract_data)
    created_contract = contract_repository.create_contract(db, db_contract)
    sync_payments(db, created_contract)  # Crear registros de pago asociados
    return created_contract

def create_library_item(db: Session, item_data: dict, tipo: str):
    """
    Crea un elemento de biblioteca (cláusula o plantilla).
    
    Prefijos de ID:
    - PLT-xxxx para plantillas
    - LIB-xxxx para cláusulas
    
    Las cláusulas guardan su contenido en 'clauses' como JSON simple.
    Las plantillas guardan una lista de cláusulas en 'clauses'.
    """
    prefix_str = "PLT" if tipo == "plantilla" else "LIB"
    item_id = generate_id(db, prefix_str)

    if tipo == "plantilla":
        clauses_content = item_data.get("clauses")  # Lista de cláusulas para plantilla
    else:
        # Para cláusulas individuales, guardar título y texto como JSON
        clauses_content = {"titulo": item_data.get("titulo"), "texto": item_data.get("texto")}

    db_item = Contrato(
        id=item_id,
        titulo=item_data.get("titulo"),
        clauses=clauses_content,
        tipo=tipo,
        es_biblioteca=True,       # Marca como elemento de biblioteca
        estado="ACTIVO",
        fecha=date.today(),
        total=0,
        cliente_id=None,          # Los elementos de biblioteca no tienen cliente
        abogado_id=None,          # ni abogado asignado
        variables_adicionales={"areaPractica": item_data.get("tipo", "Insolvencia Económica")}
    )
    return contract_repository.create_contract(db, db_item)

def generate_contract_from_template(db: Session, plantilla_id: str, contract_data: dict):
    """
    Genera un contrato real a partir de una plantilla de biblioteca.
    
    1. Busca la plantilla por ID
    2. Valida que sea realmente una plantilla de biblioteca
    3. Crea un nuevo contrato copiando las cláusulas de la plantilla
    4. Asigna el cliente y abogado provistos en contract_data
    5. Sincroniza los pagos
    
    Retorna None si la plantilla no existe o es inválida.
    """
    template = contract_repository.get_contract_by_id(db, plantilla_id)
    if not template or not template.es_biblioteca or template.tipo != "plantilla":
        return None  # Plantilla no encontrada o inválida

    new_id = generate_id(db, "CNT")
    new_contract_data = {
        "id": new_id,
        "titulo": f"Contrato basado en {template.titulo}",  # Título automático
        "cliente_id": contract_data.get("cliente_id"),
        "abogado_id": contract_data.get("abogado_id"),
        "tipo": "contrato",
        "es_biblioteca": False,          # El contrato generado es real, no de biblioteca
        "estado": "BORRADOR",            # Inicia en estado borrador
        "clauses": template.clauses,     # Copia las cláusulas de la plantilla
        "total": contract_data.get("total"),
        "variables_adicionales": contract_data.get("variables_adicionales")
    }
    db_contract = Contrato(**new_contract_data)
    created_contract = contract_repository.create_contract(db, db_contract)
    sync_payments(db, created_contract)
    return created_contract

def update_contract(db: Session, contract_id: str, contract_update: dict):
    """
    Actualiza un contrato o elemento de biblioteca existente.
    
    Para elementos de biblioteca (cláusulas/plantillas), hay lógica especial:
    - En cláusulas: el campo 'texto' se mapea a la estructura JSONB de 'clauses'
    - El campo 'tipo' se mapea a 'areaPractica' en variables_adicionales
    
    Para el resto, itera los campos enviados y los actualiza directamente.
    Después de actualizar, sincroniza los pagos si aplica.
    """
    db_contract = contract_repository.get_contract_by_id(db, contract_id)
    if not db_contract: return None
    
    # === LÓGICA ESPECIAL PARA ELEMENTOS DE BIBLIOTECA ===
    if db_contract.es_biblioteca:
        # Para cláusulas: mapear 'texto' al JSONB de clauses
        if db_contract.tipo == "clausula" and "texto" in contract_update:
            db_contract.clauses = {
                "titulo": contract_update.get("titulo", db_contract.titulo),
                "texto": contract_update["texto"]
            }
        
        # Mapear 'tipo' (área de práctica) a variables_adicionales
        if "tipo" in contract_update:
            # Crear un NUEVO dict para que SQLAlchemy detecte el cambio en el JSONB
            vars_adicionales = dict(db_contract.variables_adicionales or {})
            vars_adicionales["areaPractica"] = contract_update["tipo"]
            db_contract.variables_adicionales = vars_adicionales

    # === ACTUALIZACIÓN GENERAL DE CAMPOS ===
    for key, value in contract_update.items():
        # Saltar campos ya procesados especialmente para elementos de biblioteca
        if key in ["texto", "tipo"] and db_contract.es_biblioteca:
            continue
        if value is not None and hasattr(db_contract, key):
            if key == "estado":
                value = str(value).upper()  # Normalizar estado a mayúsculas
            setattr(db_contract, key, value)
            
    updated_contract = contract_repository.update_contract(db, db_contract)
    sync_payments(db, updated_contract)  # Resincronizar pagos con los nuevos datos
    return updated_contract
