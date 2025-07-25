"""
Endpoints para la gestión de perfiles de usuario.
"""
from fastapi import APIRouter, HTTPException
from ..database import db_usuarios
from .. import schemas

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"]
)

@router.get("/{usuario_id}", summary="Obtener datos de perfil de un usuario por ID.")
async def obtener_perfil_usuario(usuario_id: str):
    for user_data in db_usuarios.values():
        if user_data["id"] == usuario_id:
            perfil = user_data.copy()
            perfil.pop("password")
            return perfil
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.put("/{usuario_id}", summary="Actualizar datos de perfil de un usuario por ID.")
async def actualizar_perfil_usuario(usuario_id: str, datos_actualizados: schemas.PerfilUsuarioUpdate):
    for username, user_data in db_usuarios.items():
        if user_data["id"] == usuario_id:
            update_data = datos_actualizados.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if value is not None:
                    db_usuarios[username][key] = value
            return {"mensaje": "Perfil actualizado correctamente"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")