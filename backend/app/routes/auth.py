# ============================================================
# RUTAS DE AUTENTICACIÓN - routes/auth.py
# Endpoints públicos y protegidos relacionados con login,
# recuperación y restablecimiento de contraseña.
# ============================================================

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm  # Formulario estándar OAuth2 (username + password)
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from jose import JWTError, jwt

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash, validate_password_strength
from app.core.config import SECRET_KEY, ALGORITHM
from app.core.email import send_password_reset_email    # Función para enviar correo de recuperación
from app.schemas.auth import Token, ForgotPasswordRequest, ResetPasswordRequest
from app.repositories import user_repository
from app.services import auth_service
from app.models.auth import Usuario

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    ENDPOINT DE LOGIN: POST /token
    
    Recibe correo (como username) y contraseña en formato de formulario.
    Flujo de autenticación:
    1. Busca al usuario por correo
    2. Verifica el estado de la cuenta (activa, bloqueada, inactiva)
    3. Compara la contraseña con bcrypt
    4. Si falla 3 veces seguidas → bloquea la cuenta
    5. Si es correcta → resetea intentos, actualiza última conexión y retorna el JWT
    """
    user = user_repository.get_user_by_email(db, email=form_data.username)
    
    if not user:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    if user.estado == "Bloqueado":
        raise HTTPException(status_code=403, detail="Cuenta bloqueada temporalmente")

    if user.estado == "Inactivo":
        raise HTTPException(status_code=403, detail="Su cuenta ha sido desactivada. Contacte al administrador.")

    if not verify_password(form_data.password, user.password):
        # Incrementar contador de intentos fallidos
        user.intentos_fallidos += 1
        if user.intentos_fallidos >= 3:
            # Bloquear cuenta después de 3 intentos fallidos
            user.estado = "Bloqueado"
            db.add(user)
            db.commit()
            raise HTTPException(status_code=403, detail="Cuenta bloqueada temporalmente")
        
        db.add(user)
        db.commit()
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    # Login exitoso: reiniciar intentos y registrar última conexión
    user.intentos_fallidos = 0
    user.ultima_conexion = func.now()
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generar token JWT con el ID del usuario como sujeto ('sub')
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,  # Tarea en segundo plano para no bloquear la respuesta
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: POST /forgot-password
    
    Inicia el flujo de recuperación de contraseña.
    Si el correo existe, genera un token de reset y lo envía por email.
    La respuesta siempre es la misma (existe o no el correo) para
    evitar que un atacante descubra qué correos están registrados.
    El envío del correo se hace en segundo plano para responder rápido.
    """
    user = user_repository.get_user_by_email(db, email=request.correo)
    if not user:
        # Respuesta genérica por seguridad (no revelar si el correo existe)
        return {"message": "Si el correo está registrado, recibirás instrucciones brevemente"}
    
    # Crear token JWT especial solo para reset de contraseña (expira en 30 min)
    token_data = {"sub": str(user.id), "action": "reset_password"}
    token = create_access_token(data=token_data, expires_delta=timedelta(minutes=30))
    
    # Construir el enlace de recuperación que se envía al correo
    reset_link = f"http://localhost:5173/reset-password/{token}"
    full_name = f"{user.nombre} {user.apellido}"
    
    # Enviar el correo en segundo plano (no bloquea la respuesta HTTP)
    background_tasks.add_task(send_password_reset_email, user.correo, full_name, reset_link)
    
    return {"message": "Si el correo está registrado, recibirás instrucciones brevemente"}

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: POST /reset-password
    
    Restablece la contraseña usando el token recibido por correo.
    1. Decodifica y valida el token JWT
    2. Verifica que el token sea específicamente de reset (action='reset_password')
    3. Valida la fortaleza de la nueva contraseña
    4. Actualiza la contraseña en la BD y reactiva la cuenta si estaba bloqueada
    """
    try:
        # Decodificar el token usando la clave secreta
        payload = jwt.decode(request.token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        action = payload.get("action")
        
        # Verificar que sea un token de reset válido
        if user_id is None or action != "reset_password":
            raise HTTPException(status_code=400, detail="Token inválido o expirado")
            
        validate_password_strength(request.new_password)  # Validar requisitos de la nueva contraseña
        user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        # Actualizar contraseña y reactivar cuenta
        auth_service.update_user(db, db_user=user, user_update={
            "password": request.new_password, 
            "estado": "Activo"  # Desbloquear cuenta si estaba bloqueada
        })
        
        return {"message": "Contraseña restablecida exitosamente"}
        
    except (JWTError, ValueError):
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
