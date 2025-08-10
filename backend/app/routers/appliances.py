"""
Endpoints para la gestión de electrodomésticos usando Supabase
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from frontend.services import api_client  

router = APIRouter(
    tags=["electrodomesticos"]
)

# Modelos Pydantic
class ElectrodomesticoBase(BaseModel):
    nombre: str
    cantidad: int
    potencia: float
    eficiencia: Optional[str] = "A"
    horas_dia: float
    dias_mes: int

class ElectrodomesticoCreate(ElectrodomesticoBase):
    usuario_id: str

class Electrodomestico(ElectrodomesticoCreate):
    id: str
    created_at: datetime

class ElectrodomesticoUpdate(BaseModel):
    nombre: Optional[str] = None
    cantidad: Optional[int] = None
    potencia: Optional[float] = None
    eficiencia: Optional[str] = None
    horas_dia: Optional[float] = None
    dias_mes: Optional[int] = None

@router.get("/electrodomesticos/{usuario_id}", response_model=List[Electrodomestico],
           summary="Obtener electrodomésticos de un usuario")
async def obtener_electrodomesticos(usuario_id: str):
    try:
        response = supabase = api_client.get_supabase_client()
        response = supabase.table("electrodomesticos")\
                         .select("*")\
                         .eq("usuario_id", usuario_id)\
                         .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No se encontraron electrodomésticos")
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")

@router.post("/electrodomesticos", response_model=Electrodomestico,
            summary="Añadir nuevo electrodoméstico")
async def crear_electrodomestico(electrodomestico: ElectrodomesticoCreate):
    try:
        # Convertir a dict y asegurar tipos correctos
        data = electrodomestico.dict()
        data["cantidad"] = int(data["cantidad"])
        data["dias_mes"] = int(data["dias_mes"])
        
        response = supabase = api_client.get_supabase_client()
        response = supabase.table("electrodomesticos")\
                         .insert(data)\
                         .execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="No se pudo crear el electrodoméstico")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear: {str(e)}")

@router.put("/electrodomesticos/{electrodomestico_id}", response_model=Electrodomestico,
           summary="Actualizar electrodoméstico")
async def actualizar_electrodomestico(electrodomestico_id: str, datos: ElectrodomesticoUpdate):
    try:
        # Filtrar campos None para actualización parcial
        update_data = {k: v for k, v in datos.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")
        
        response = supabase = api_client.get_supabase_client()
        response = supabase.table("electrodomesticos")\
                         .update(update_data)\
                         .eq("id", electrodomestico_id)\
                         .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Electrodoméstico no encontrado")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

@router.delete("/electrodomesticos/{electrodomestico_id}",
              summary="Eliminar electrodoméstico")
async def eliminar_electrodomestico(electrodomestico_id: str):
    try:
        response = supabase = api_client.get_supabase_client()
        response = supabase.table("electrodomesticos")\
                         .delete()\
                         .eq("id", electrodomestico_id)\
                         .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Electrodoméstico no encontrado")
        return {"mensaje": "Electrodoméstico eliminado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

# Endpoint para el catálogo base (opcional)
@router.get("/catalogo/electrodomesticos",
           summary="Obtener catálogo base de electrodomésticos")
async def obtener_catalogo():
    # Esto puede mantenerse en memoria o moverse a otra tabla en Supabase
    catalogo_base = [
        {"nombre": "Refrigerador", "potencia_base": 150, "horas_dia_estandar": 24, "dias_mes_estandar": 30},
        {"nombre": "Televisor", "potencia_base": 100, "horas_dia_estandar": 4, "dias_mes_estandar": 30},
        # ... otros electrodomésticos base
    ]
    return catalogo_base