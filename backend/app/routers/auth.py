"""
Endpoints para la autenticación de usuarios: registro e inicio de sesión.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from .. import schemas
from ..database import db_usuarios

router = APIRouter()

@router.post("/login", summary="Autenticar un usuario.")
async def login(peticion: schemas.PeticionLogin):
    if peticion.username in db_usuarios and db_usuarios[peticion.username]["password"] == peticion.password:
        return {"mensaje": "Inicio de sesión exitoso", "usuario_id": db_usuarios[peticion.username]["id"]}
    raise HTTPException(status_code=401, detail="Credenciales incorrectas")

@router.post("/registro", summary="Registrar un nuevo usuario.")
async def registro(peticion: schemas.PeticionRegistro):
    if peticion.username in db_usuarios:
        raise HTTPException(status_code=409, detail="El usuario ya existe")
    
    nuevo_usuario_id = f"user-{uuid.uuid4().hex[:8]}"
    db_usuarios[peticion.username] = {
        "id": nuevo_usuario_id,
        "username": peticion.username,
        "password": peticion.password,
        "nombre": peticion.nombre,
        "ubicacion": peticion.ubicacion,
        "nivel_subsidio": peticion.nivel_subsidio,
        "facturas": [],
        "electrodomesticos": [],
        "puntos_sostenibilidad": 0,
        "consejos_cumplidos": [],
        "progreso_sostenibilidad": [{"fecha": datetime.now().strftime("%Y-%m-%d"), "puntos": 0}]
    }
    return {"mensaje": "Usuario registrado correctamente", "usuario_id": nuevo_usuario_id}