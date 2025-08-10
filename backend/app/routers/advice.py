"""
Endpoints para la gestión de consejos de sostenibilidad.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from .. import schemas, utils
from ..database import db_usuarios

router = APIRouter(
    prefix="/consejos",
    tags=["consejos"]
)

@router.get("/{usuario_id}", summary="Obtener consejos de sostenibilidad para un usuario.")
async def obtener_consejos(usuario_id: str):
    user_data = next((u for u in db_usuarios.values() if u["id"] == usuario_id), None)
    if user_data:
        consumo = sum(f["consumo_kwh"] for f in user_data.get("facturas", []))
        huella = utils.calcular_huella_carbono(consumo)
        
        consejos = utils.generar_consejos_dinamicos(
            consumo, huella, user_data["puntos_sostenibilidad"], user_data["consejos_cumplidos"]
        )
        return {"consejos": consejos, "puntos_sostenibilidad": user_data["puntos_sostenibilidad"]}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.post("/{username}/marcar_cumplido", summary="Marcar un consejo como cumplido.")
async def marcar_consejo_cumplido(username: str, peticion: schemas.MarcarConsejoCumplido):
    if user_data := db_usuarios.get(username):
        consejo_id = peticion.consejo_id
        if consejo_id not in user_data["consejos_cumplidos"]:
            user_data["consejos_cumplidos"].append(consejo_id)
            user_data["puntos_sostenibilidad"] += 10
            
            hoy = datetime.now().strftime("%Y-%m-%d")
            progreso = user_data["progreso_sostenibilidad"]
            if progreso and progreso[-1]["fecha"] == hoy:
                progreso[-1]["puntos"] = user_data["puntos_sostenibilidad"]
            else:
                progreso.append({"fecha": hoy, "puntos": user_data["puntos_sostenibilidad"]})
                
            return {"mensaje": "Consejo cumplido", "puntos_actuales": user_data["puntos_sostenibilidad"]}
        return {"mensaje": "Consejo ya estaba cumplido"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")