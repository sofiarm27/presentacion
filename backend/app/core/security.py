# ============================================================
# SEGURIDAD Y AUTENTICACIÓN - security.py
# Maneja el cifrado de contraseñas, creación y validación
# de tokens JWT, y verificación del usuario autenticado.
# ============================================================

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt                          # Librería para crear y decodificar tokens JWT
from passlib.context import CryptContext                # Librería para cifrar contraseñas con bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer       # Esquema de autenticación OAuth2 con Bearer token
from sqlalchemy.orm import Session
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.database import get_db
from app.models.auth import Usuario

# Contexto de cifrado usando el algoritmo bcrypt (estándar de seguridad para contraseñas)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Indica a FastAPI dónde está el endpoint de login (para la documentación Swagger)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    """
    Verifica si la contraseña en texto plano coincide con la versión cifrada.
    Se usa al momento del login.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Cifra una contraseña con bcrypt antes de guardarla en la base de datos.
    Nunca se almacenan contraseñas en texto plano.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Crea un token JWT firmado con la clave secreta.
    El token contiene el ID del usuario ('sub') y su fecha de expiración.
    Por defecto expira en ACCESS_TOKEN_EXPIRE_MINUTES (30 min).
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Dependencia que se inyecta en cada endpoint protegido.
    Decodifica el token JWT, busca al usuario en la base de datos
    y verifica que su cuenta esté activa.
    Lanza HTTP 401 si el token es inválido o expiró.
    Lanza HTTP 403 si la cuenta está inactiva o bloqueada.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica el token usando la clave secreta y el algoritmo configurado
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")  # 'sub' contiene el ID del usuario
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Intentar convertir el ID a entero (los tokens nuevos guardan el ID numérico)
    try:
        user_id_int = int(user_id)
    except ValueError:
        # Compatibilidad con tokens antiguos que guardaban el correo en lugar del ID
        user = db.query(Usuario).filter(Usuario.correo == user_id).first()
        if user:
            return user
        raise credentials_exception

    # Buscar el usuario en la base de datos por su ID
    user = db.query(Usuario).filter(Usuario.id == user_id_int).first()
    if user is None:
        raise credentials_exception

    # Verificar que la cuenta no esté desactivada por el administrador
    if user.estado == "Inactivo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Su cuenta ha sido desactivada. Contacte al administrador."
        )
    
    # Verificar que la cuenta no esté bloqueada por intentos fallidos
    if user.estado == "Bloqueado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta bloqueada temporalmente"
        )

    return user  # Retorna el objeto usuario para usarlo en el endpoint

def check_admin_role(current_user: Usuario = Depends(get_current_user)):
    """
    Dependencia adicional para restringir endpoints solo a administradores.
    Lanza HTTP 403 si el usuario autenticado no tiene rol 'administrador'.
    """
    user_roles = [r.nombre.lower() for r in current_user.roles]
    if "administrador" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para acceder a este recurso"
        )
    return current_user

import re
def validate_password_strength(password: str):
    """
    Valida que la contraseña cumpla con los requisitos mínimos de seguridad:
    - Al menos 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un carácter especial
    Lanza HTTP 400 si no cumple los requisitos.
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres"
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos una letra mayúscula"
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos una letra minúscula"
        )
    if not re.search(r"[0-9]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos un número"
        )
    if not re.search(r"[@$!%*?&._\-#^&+=\[\]{}()|\\\:;<>~`/,]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos un carácter especial (@$!%*?&._-#^&+=...)"
        )
    return True
