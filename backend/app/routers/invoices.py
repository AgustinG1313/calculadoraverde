"""
Endpoints para la gestión de facturas de un usuario.
"""
from fastapi import APIRouter, HTTPException
from .. import schemas
from ..database import db_usuarios

router = APIRouter(
    prefix="/facturas",
    tags=["facturas"]
)

@router.get("/{username}", summary="Obtener todas las facturas de un usuario.")
async def obtener_facturas(username: str):
    if user_data := db_usuarios.get(username):
        return user_data["facturas"]
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.post("/{username}", summary="Añadir una nueva factura para un usuario.")
async def anadir_factura(username: str, factura: schemas.Factura):
    if username in db_usuarios:
        db_usuarios[username]["facturas"].append(factura.model_dump())
        return {"mensaje": "Factura añadida correctamente"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.delete("/{username}/{factura_id}", summary="Eliminar una factura de un usuario.")
async def eliminar_factura(username: str, factura_id: str):
    if user_data := db_usuarios.get(username):
        original_count = len(user_data["facturas"])
        user_data["facturas"] = [f for f in user_data["facturas"] if f["id"] != factura_id]
        if len(user_data["facturas"]) < original_count:
            return {"mensaje": "Factura eliminada correctamente"}
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    raise HTTPException(status_code=404, detail="Usuario no encontrado")