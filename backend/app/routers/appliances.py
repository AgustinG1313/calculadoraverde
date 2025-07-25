"""
Endpoints para la gestión de electrodomésticos y el catálogo base.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict
from .. import schemas
from ..database import db_usuarios, BASE_ELECTRODOMESTICOS

router = APIRouter(
    tags=["electrodomesticos"]
)

@router.get("/electrodomesticos/{username}", summary="Obtener todos los electrodomésticos de un usuario.")
async def obtener_electrodomesticos_usuario(username: str):
    if user_data := db_usuarios.get(username):
        return user_data["electrodomesticos"]
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.post("/electrodomesticos/{username}", summary="Añadir un nuevo electrodoméstico.")
async def anadir_electrodomestico(username: str, electrodomestico: schemas.Electrodomestico):
    if username in db_usuarios:
        db_usuarios[username]["electrodomesticos"].append(electrodomestico.model_dump())
        return {"mensaje": "Electrodoméstico añadido correctamente"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.put("/electrodomesticos/{username}/{electrodomestico_id}", summary="Actualizar un electrodoméstico.")
async def actualizar_electrodomestico(username: str, electrodomestico_id: str, datos: Dict):
    if user_data := db_usuarios.get(username):
        for i, ed in enumerate(user_data["electrodomesticos"]):
            if ed["id"] == electrodomestico_id:
                user_data["electrodomesticos"][i].update(datos)
                return {"mensaje": "Electrodoméstico actualizado"}
        raise HTTPException(status_code=404, detail="Electrodoméstico no encontrado")
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.delete("/electrodomesticos/{username}/{electrodomestico_id}", summary="Eliminar un electrodoméstico.")
async def eliminar_electrodomestico(username: str, electrodomestico_id: str):
    if user_data := db_usuarios.get(username):
        original_count = len(user_data["electrodomesticos"])
        user_data["electrodomesticos"] = [ed for ed in user_data["electrodomesticos"] if ed["id"] != electrodomestico_id]
        if len(user_data["electrodomesticos"]) < original_count:
            return {"mensaje": "Electrodoméstico eliminado"}
        raise HTTPException(status_code=404, detail="Electrodoméstico no encontrado")
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.get("/catalogo/electrodomesticos", summary="Obtener el catálogo de electrodomésticos.")
async def obtener_catalogo_electrodomesticos():
    return BASE_ELECTRODOMESTICOS