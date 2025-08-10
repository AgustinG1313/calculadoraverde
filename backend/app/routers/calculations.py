"""
Endpoints para realizar cálculos de costo y huella de carbono.
"""
from fastapi import APIRouter
from .. import schemas, utils
from ..database import db_usuarios

router = APIRouter(
    prefix="/calcular",
    tags=["calculos"]
)

@router.post("/costo", summary="Calcular costo estimado basado en kWh y subsidio.")
async def calcular_costo_endpoint(peticion: schemas.CalculoKWH):
    user_location = "Resistencia, Chaco"
    for user in db_usuarios.values():
        if user["nivel_subsidio"] == peticion.nivel_subsidio:
            user_location = user["ubicacion"]
            break
            
    costo_calculado = utils.calcular_costo_rango(peticion.kwh, peticion.nivel_subsidio, user_location)
    return {"costo_estimado": costo_calculado}

@router.post("/huella_carbono", summary="Calcular huella de carbono basada en kWh.")
async def calcular_huella_carbono_endpoint(peticion: schemas.CalculoKWH):
    huella = utils.calcular_huella_carbono(peticion.kwh)
    return {"huella_carbono_kg_co2": huella}