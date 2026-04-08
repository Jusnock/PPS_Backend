import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.core.config import settings
from app.core.database import get_db
from app.models import models

# --- CONFIGURACIÓN DE CRIPTOGRAFÍA ---
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Motor de encriptación Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer()

# --- FUNCIONES DE CONTRASEÑAS ---
def verify_password(plain_password, hashed_password):
    """Verifica si la contraseña ingresada coincide con el hash guardado"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Genera un hash seguro a partir de una contraseña en texto plano"""
    return pwd_context.hash(password)

# --- FUNCIONES DE TOKENS Y SESIÓN ---
def create_access_token(data: dict):
    """Genera el token JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme), db: Session = Depends(get_db)):
    """Desencripta el JWT, verifica quién es y devuelve el usuario de la BD"""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token ha expirado")
    except jwt.InvalidTokenError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

def get_current_superadmin(current_user: models.User = Depends(get_current_user)):
    """Candado adicional: Verifica que el usuario tenga el rol de SUPERADMIN"""
    if current_user.rol != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operación denegada. Se requieren privilegios de Super Administrador."
        )
    return current_user

def get_current_admin_empresa(current_user: models.User = Depends(get_current_user)):
    """Candado: Permite el paso al Admin de la Empresa cliente (y al SuperAdmin)"""
    if current_user.rol not in ["SUPERADMIN", "ADMIN_EMPRESA"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operación denegada. Se requieren privilegios de Administrador."
        )
    return current_user