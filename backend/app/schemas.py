"""
Define los esquemas de Pydantic utilizados para la validación de datos
en las solicitudes y respuestas de la API.
"""
from pydantic import BaseModel
from typing import List, Dict

class PeticionLogin(BaseModel):
    username: str
    password: str

class PeticionRegistro(BaseModel):
    username: str
    password: str
    nombre: str
    ubicacion: str
    nivel_subsidio: str

class Factura(BaseModel):
    id: str
    mes: str
    anio: int
    consumo_kwh: float
    costo: float

class Electrodomestico(BaseModel):
    id: str
    nombre: str
    cantidad: int
    potencia: float
    eficiencia: str
    horas_dia: float
    dias_mes: int

class CalculoKWH(BaseModel):
    kwh: float
    nivel_subsidio: str = "medio"

class MarcarConsejoCumplido(BaseModel):
    consejo_id: str

class PerfilUsuarioUpdate(BaseModel):
    nombre: str | None = None
    ubicacion: str | None = None
    nivel_subsidio: str | None = None
    password: str | None = None