import pandas as pd
import random
import uuid
from datetime import datetime
from typing import Optional, List, Dict
import functools
from fastapi import FastAPI, HTTPException
from frontend.services.api_client import get_supabase_client, cargar_datos_facturas
from frontend.services.api_client import cargar_datos_electrodomesticos
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# - INICIALIZACIÓN DE LA APP -
app = FastAPI(
    title="BioTrack API",
    description="API para gestionar datos de consumo energético y sostenibilidad.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PeticionLogin(BaseModel):
    username: str
    password: str

class PeticionRegistro(BaseModel):
    email: str  # Cambiado de username a email
    password: str
    nombre: str
    ubicacion: str
    nivel_subsidio: str
    personas: Optional[int] = None  # Nuevo campo
    lat: Optional[float] = None    # Nuevo campo
    lon: Optional[float] = None    # Nuevo campo

class Factura(BaseModel):
    mes: str
    anio: int
    consumo_kwh: float
    costo: float

class FacturaDB(Factura):
    id: str
    usuario_id: str
    created_at: datetime
    
class Electrodomestico(BaseModel):
    nombre: str
    cantidad: int
    potencia: float
    eficiencia: str
    horas_dia: float
    dias_mes: int

class ElectrodomesticoDB(Electrodomestico):
    id: str
    usuario_id: str
    
    
class CalculoKWH(BaseModel):
    kwh: float
    nivel_subsidio: str = "medio"

class MarcarConsejoCumplido(BaseModel):
    consejo_id: str

# - BASE DE DATOS SIMULADA -
db_usuarios = {
    "usuario1@example.com": {
        "id": "user-abc123def456",
        "username": "usuario1@example.com",
        "password": "password123",
        "nombre": "Ana García",
        "ubicacion": "Resistencia, Chaco",
        "nivel_subsidio": "medio",
        "facturas": [],
        "electrodomesticos": [],
        "puntos_sostenibilidad": 0,
        "consejos_cumplidos": [],
        "progreso_sostenibilidad": [{"fecha": "2024-01-01", "puntos": 0}]
    }
}

BASE_ELECTRODOMESTICOS = [
    {"id": "cat-001", "nombre": "Heladera c/freezer (moderno)", "potencia_base": 150, "eficiencia_estandar": "Alta", "horas_dia_estandar": 8, "dias_mes_estandar": 30},
    {"id": "cat-002", "nombre": "Freezer independiente", "potencia_base": 250, "eficiencia_estandar": "Baja", "horas_dia_estandar": 7.2, "dias_mes_estandar": 30},
    {"id": "cat-003", "nombre": "Heladera sin freezer", "potencia_base": 150, "eficiencia_estandar": "Baja", "horas_dia_estandar": 7.2, "dias_mes_estandar": 30},
    {"id": "cat-004", "nombre": "Aire Acond. Split 2200 fg Inv", "potencia_base": 877.5, "eficiencia_estandar": "Alta", "horas_dia_estandar": 1.5, "dias_mes_estandar": 30},
    {"id": "cat-005", "nombre": "Aire Acond. Split 2200 fg On/Off", "potencia_base": 1350, "eficiencia_estandar": "Baja", "horas_dia_estandar": 1.5, "dias_mes_estandar": 30},
    {"id": "cat-006", "nombre": "Lavadora Automática (sin agua)", "potencia_base": 500, "eficiencia_estandar": "Alta", "horas_dia_estandar": 0.5, "dias_mes_estandar": 10},
    {"id": "cat-007", "nombre": "Lavadora c/calefacción", "potencia_base": 2500, "eficiencia_estandar": "Baja", "horas_dia_estandar": 0.5, "dias_mes_estandar": 10},
    {"id": "cat-008", "nombre": "Horno eléctrico 30L", "potencia_base": 1500, "eficiencia_estandar": "Alta", "horas_dia_estandar": 0.75, "dias_mes_estandar": 15},
    {"id": "cat-009", "nombre": "Horno eléctrico empotrado", "potencia_base": 2450, "eficiencia_estandar": "Baja", "horas_dia_estandar": 0.75, "dias_mes_estandar": 15},
    {"id": "cat-010", "nombre": "Termotanque eléctrico", "potencia_base": 1500, "eficiencia_estandar": "Baja", "horas_dia_estandar": 1.3, "dias_mes_estandar": 30},
    {"id": "cat-011", "nombre": "Calefón eléctrico", "potencia_base": 1800, "eficiencia_estandar": "Baja", "horas_dia_estandar": 0.7, "dias_mes_estandar": 30},
    {"id": "cat-012", "nombre": "Lámpara LED 11W", "potencia_base": 11, "eficiencia_estandar": "Alta", "horas_dia_estandar": 6.0, "dias_mes_estandar": 30},
    {"id": "cat-013", "nombre": "Tubo fluorescente 58W", "potencia_base": 58, "eficiencia_estandar": "Baja", "horas_dia_estandar": 6.0, "dias_mes_estandar": 30},
    {"id": "cat-014", "nombre": "Lámpara bajo consumo 20W", "potencia_base": 20, "eficiencia_estandar": "Baja", "horas_dia_estandar": 6.0, "dias_mes_estandar": 30},
    {"id": "cat-015", "nombre": "CPU de escritorio", "potencia_base": 200, "eficiencia_estandar": "Media", "horas_dia_estandar": 4.0, "dias_mes_estandar": 30},
    {"id": "cat-016", "nombre": "Monitor LED 19\"", "potencia_base": 22, "eficiencia_estandar": "Alta", "horas_dia_estandar": 4.0, "dias_mes_estandar": 30},
    {"id": "cat-017", "nombre": "Laptop/Notebook", "potencia_base": 60, "eficiencia_estandar": "Alta", "horas_dia_estandar": 4.0, "dias_mes_estandar": 30},
    {"id": "cat-018", "nombre": "Pava eléctrica", "potencia_base": 2000, "eficiencia_estandar": "Alta", "horas_dia_estandar": 0.1, "dias_mes_estandar": 30},
    {"id": "cat-019", "nombre": "Plancha", "potencia_base": 1500, "eficiencia_estandar": "Media", "horas_dia_estandar": 0.5, "dias_mes_estandar": 10},
    {"id": "cat-020", "nombre": "Secarropas térmico", "potencia_base": 950, "eficiencia_estandar": "Media", "horas_dia_estandar": 1.0, "dias_mes_estandar": 10},
    {"id": "cat-021", "nombre": "Secarropas centrífugo", "potencia_base": 380, "eficiencia_estandar": "Media", "horas_dia_estandar": 1.0, "dias_mes_estandar": 10},
    {"id": "cat-022", "nombre": "Lavavajillas 12 cubiertos", "potencia_base": 1500, "eficiencia_estandar": "Baja", "horas_dia_estandar": 1.5, "dias_mes_estandar": 15},
    {"id": "cat-023", "nombre": "Bomba de agua 1/2 HP", "potencia_base": 380, "eficiencia_estandar": "Media", "horas_dia_estandar": 1.0, "dias_mes_estandar": 30},
    {"id": "cat-024", "nombre": "Bomba de agua 3/4 HP", "potencia_base": 570, "eficiencia_estandar": "Media", "horas_dia_estandar": 1.0, "dias_mes_estandar": 30},
    {"id": "cat-025", "nombre": "Anafe vitrocerámico", "potencia_base": 2350, "eficiencia_estandar": "Alta", "horas_dia_estandar": 0.5, "dias_mes_estandar": 30},
    {"id": "cat-026", "nombre": "Anafe resistivo", "potencia_base": 2000, "eficiencia_estandar": "Baja", "horas_dia_estandar": 0.5, "dias_mes_estandar": 30},
    {"id": "cat-027", "nombre": "Cafetera eléctrica filtro", "potencia_base": 900, "eficiencia_estandar": "Alta", "horas_dia_estandar": 0.25, "dias_mes_estandar": 10},
    {"id": "cat-028", "nombre": "Secador de cabello", "potencia_base": 2000, "eficiencia_estandar": "Media", "horas_dia_estandar": 0.2, "dias_mes_estandar": 6},
    {"id": "cat-029", "nombre": "Tostadora", "potencia_base": 950, "eficiencia_estandar": "Alta", "horas_dia_estandar": 0.1, "dias_mes_estandar": 30},
    {"id": "cat-030", "nombre": "Cargador de celular", "potencia_base": 5, "eficiencia_estandar": "Alta", "horas_dia_estandar": 6.0, "dias_mes_estandar": 30},
    {"id": "cat-031", "nombre": "Consola en standby", "potencia_base": 100, "eficiencia_estandar": "Baja", "horas_dia_estandar": 2.0, "dias_mes_estandar": 30},
    {"id": "cat-032", "nombre": "Router WiFi", "potencia_base": 10, "eficiencia_estandar": "Alta", "horas_dia_estandar": 24.0, "dias_mes_estandar": 30},
]

# - FUNCIONES AUXILIARES DE CÁLCULO -
@functools.lru_cache(maxsize=128)
def calcular_costo_rango(kwh: float, nivel_subsidio: str, ubicacion: str = "Resistencia, Chaco") -> float:
    cargo_fijo = 2277.3100  # $/mes para Chaco
    costo_total_kwh = 0.0

    tarifas_urbanas_n1 = [
        (50, 118.6888),
        (100, 126.6517),
        (150, 151.4252),
        (float('inf'), 163.8120)
    ]
    tarifas_urbanas_n2 = [
        (50, 52.0293),
        (100, 59.9922),
        (150, 84.7657),
        (50, 97.1525),
        (float('inf'), 163.8120)
    ]
    tarifas_urbanas_n3 = [
        (50, 67.1414),
        (100, 75.1043),
        (100, 99.8778),
        (50, 151.4252),
        (float('inf'), 163.8120)
    ]

    tarifas_rurales = {
        "alto": [(float('inf'), 147.4494)],
        "bajo": [(350, 81.7632), (float('inf'), 147.4494)],
        "medio": [(250, 96.6547), (float('inf'), 147.4494)]
    }

    if "Chaco" in ubicacion:
        current_month = datetime.now().month
        is_summer = current_month in [1, 2, 3, 12]
        
        applied_tiers = []
        if "Rural" in ubicacion:
            applied_tiers = tarifas_rurales[nivel_subsidio]
        else: # urbano
            if nivel_subsidio == "bajo":
                applied_tiers = tarifas_urbanas_n2
            elif nivel_subsidio == "medio":
                applied_tiers = tarifas_urbanas_n3
            else: # nivel_subsidio == "alto"
                applied_tiers = tarifas_urbanas_n1
        
        remaining_kwh = kwh

        for block_size, rate in applied_tiers:
            if remaining_kwh <= 0:
                break

            consumed_in_block = min(remaining_kwh, block_size) if block_size != float('inf') else remaining_kwh
            
            current_rate = rate

            if "Rural" not in ubicacion: 
                if is_summer: # vernao (Ene, Feb, Mar, Dic)
                    if kwh <= 300:
                        current_rate *= (1 - 0.60)
                    elif kwh <= 450:
                        current_rate *= (1 - 0.50)
                else: 
                    if kwh <= 200:
                        current_rate *= (1 - 0.60)
                    elif kwh <= 300:
                        current_rate *= (1 - 0.50)

            costo_total_kwh += consumed_in_block * current_rate
            remaining_kwh -= consumed_in_block
        
        costo_final = costo_total_kwh + cargo_fijo 

        #  "Descuento Verano"
        if is_summer and nivel_subsidio in ["bajo", "medio"]:
            if kwh <= 600:
                costo_final *= (1 - 0.29)
            elif kwh <= 800:
                costo_final *= (1 - 0.22)
            elif kwh <= 1000:
                costo_final *= (1 - 0.15)
    
    else: 
        tarifa_base_n1 = 106.879 # ARS por kWh (referencia de EDESUR Dic 2024)
        
        if nivel_subsidio == "bajo": # Nivel 2 (N2 - Bajos Ingresos)
            limite_subsidio = 350 # kWh/mes
            bonificacion_n2 = 0.6815 # 68.15%
            if kwh <= limite_subsidio:
                costo_total_kwh = kwh * tarifa_base_n1 * (1 - bonificacion_n2)
            else:
                costo_total_kwh = (limite_subsidio * tarifa_base_n1 * (1 - bonificacion_n2)) + \
                                ((kwh - limite_subsidio) * tarifa_base_n1)
        elif nivel_subsidio == "medio": # Nivel 3 (N3 - Ingresos Medios)
            limite_subsidio = 250 # kWh/mes
            bonificacion_n3 = 0.5270 # 52.70%
            if kwh <= limite_subsidio:
                costo_total_kwh = kwh * tarifa_base_n1 * (1 - bonificacion_n3)
            else:
                costo_total_kwh = (limite_subsidio * tarifa_base_n1 * (1 - bonificacion_n3)) + \
                                ((kwh - limite_subsidio) * tarifa_base_n1)
        elif nivel_subsidio == "alto": # Nivel 1 (N1 - Ingresos Altos)
            costo_total_kwh = kwh * tarifa_base_n1
        
        costo_final = costo_total_kwh
        # IVA (21%)
        costo_final = costo_final * (1 + 0.21)

    return round(costo_final, 2)

@functools.lru_cache(maxsize=128)
def calcular_huella_carbono(kwh: float) -> float:
    # Factor de emisión promedio para la generación de electricidad en Argentina (ej: 0.3 kg CO2/kWh)
    factor_emision_co2 = 0.3 # kg CO2 por kWh
    huella = kwh * factor_emision_co2
    return round(huella, 2)

def generar_consejos_dinamicos(consumo_actual: float, huella_carbono_actual: float, puntos_sostenibilidad: int, consejos_cumplidos_ids: List[str]) -> List[Dict]:
    """Genera una lista de consejos de sostenibilidad personalizados."""
    all_consejos = [
        {"id": "con-001", "texto": "Apaga las luces al salir de una habitación.", "urgente": False},
        {"id": "con-002", "texto": "Desconecta los cargadores cuando no los uses (consumo vampiro).", "urgente": False},
        {"id": "con-003", "texto": "Considera usar bombillas LED de bajo consumo.", "urgente": True if consumo_actual > 200 else False},
        {"id": "con-004", "texto": "Revisa el aislamiento de tu hogar para evitar fugas de energía.", "urgente": True if consumo_actual > 300 else False},
        {"id": "con-005", "texto": "Ajusta la temperatura del aire acondicionado a 24°C en verano.", "urgente": True if consumo_actual > 250 else False},
        {"id": "con-006", "texto": "Prefiere electrodomésticos de alta eficiencia energética (Clase A o superior).", "urgente": False},
        {"id": "con-007", "texto": "Utiliza el lavarropas con carga completa y agua fría.", "urgente": False},
        {"id": "con-008", "texto": "Seca la ropa al aire libre siempre que sea posible.", "urgente": False},
        {"id": "con-009", "texto": "Descongela los alimentos en la heladera, no a temperatura ambiente.", "urgente": False},
        {"id": "con-010", "texto": "Limpia regularmente la parte trasera de tu heladera para mejorar su eficiencia.", "urgente": False},
        {"id": "con-011", "texto": "Toma duchas más cortas para ahorrar agua y energía (si usas termotanque eléctrico).", "urgente": False},
        {"id": "con-012", "texto": "Aprovecha la luz natural al máximo durante el día.", "urgente": False},
        {"id": "con-013", "texto": "Si tienes horno eléctrico, evita abrir la puerta constantemente para no perder calor.", "urgente": False},
        {"id": "con-014", "texto": "Considera instalar paneles solares si tu consumo es muy alto y es viable en tu zona.", "urgente": True if consumo_actual > 400 else False},
        {"id": "con-015", "texto": "Utiliza colores claros en paredes y techos para aprovechar mejor la iluminación natural y reducir el uso de luz artificial.", "urgente": False},
        {"id": "con-015", "texto": "Utilizar colores claros en paredes y techos para aprovechar mejor la iluminación natural y reducir el uso de luz artificial.", "urgente": False},
        {"id": "con-016", "texto": "Reducir al mínimo la iluminación decorativa, tanto interior como exterior, compatible con la seguridad.", "urgente": False},
        {"id": "con-017", "texto": "Mantener limpias las lámparas y pantallas para aumentar la luminosidad sin aumentar su potencia.", "urgente": False},
        {"id": "con-018", "texto": "Mantener limpios los vidrios de las ventanas y otros ingresos de luz natural para reducir el consumo de luz artificial.", "urgente": False},
        {"id": "con-019", "texto": "No dejar luces encendidas en espacios comunes de uso eventual si no están siendo utilizados, por más bajo que sea su consumo.", "urgente": False},
        {"id": "con-020", "texto": "Apagar las luces al retirarse el encargado si la luz natural es suficiente, y que el vecindario las encienda cuando sea necesario.", "urgente": False},
        {"id": "con-021", "texto": "Reemplazar luminarias por lámparas más eficientes como las LED cuando se quemen las actuales.", "urgente": False},
        {"id": "con-022", "texto": "Considerar reguladores de intensidad luminosa electrónicos en espacios que requieran distinta intensidad de iluminación durante el día.", "urgente": False},
        {"id": "con-023", "texto": "Instalar detectores de movimiento o células fotoeléctricas para el encendido y apagado automático de luces.", "urgente": False},
        {"id": "con-024", "texto": "Automatizar el encendido de luces en escaleras incluyendo un control sobre cada piso para evitar encendidos simultáneos.", "urgente": False},
        {"id": "con-025", "texto": "Instalar interruptores independientes para encender solo las luminarias necesarias en cada momento.", "urgente": False},
        {"id": "con-026", "texto": "El ahorro de agua, aunque no sea caliente, significa un ahorro energético, ya que es bombeada con electricidad.", "urgente": False},
        {"id": "con-027", "texto": "Incluir en el mantenimiento reparaciones para evitar goteos y fugas en accesorios, válvulas y canillas.", "urgente": False},
        {"id": "con-028", "texto": "No dejar canillas abiertas inútilmente, por ejemplo, durante la limpieza y el lavado de veredas.", "urgente": False},
        {"id": "con-029", "texto": "Considerar la incorporación de ahorradores de agua al incorporar o reemplazar accesorios y/o válvulas.", "urgente": False},
        {"id": "con-030", "texto": "Si la bomba de agua es más grande de lo necesario, evaluar cambiarla, modificarla o instalar un variador de velocidad.", "urgente": True if consumo_actual > 200 else False},
        {"id": "con-031", "texto": "Si la bomba de agua del edificio tiene más de 10 años, considerar un recambio por una tecnología más eficiente.", "urgente": False},
        {"id": "con-032", "texto": "Optar por motores más eficientes (Tipo IE3) al incorporar o reemplazar motores nuevos o existentes.", "urgente": False},
        {"id": "con-033", "texto": "Evitar reparar motores existentes más de dos o tres veces, y siempre solicitar ensayos de rendimiento.", "urgente": False},
        {"id": "con-034", "texto": "Para alturas inferiores a un tercer piso, priorizar el uso de las escaleras.", "urgente": False},
        {"id": "con-035", "texto": "Si el ascensor tiene botones separados para subir y bajar, pulsar solo el de la dirección necesaria.", "urgente": False},
        {"id": "con-036", "texto": "Dentro del ascensor, no permitir que los niños presionen todos los botones de los distintos pisos o salten.", "urgente": False},
        {"id": "con-037", "texto": "Mantener limpias las luminarias y artefactos del ascensor para aumentar la iluminación sin aumentar su potencia.", "urgente": False},
        {"id": "con-038", "texto": "Un ascensor eficiente debe incluir un sistema de accionamiento de muy baja fricción, función de ahorro de energía en reposo e iluminación LED con auto-apagado.", "urgente": False},
        {"id": "con-039", "texto": "En ascensores de gran tráfico, es aconsejable instalar un sistema de control de velocidad que recupere la energía de frenado.", "urgente": False},
        {"id": "con-040", "texto": "Bajar en 1°C el termostato en invierno puede generar un ahorro del 10% al 20% del consumo de calefacción.", "urgente": False},
        {"id": "con-041", "texto": "No calefaccionar los ambientes comunes que no se están utilizando.", "urgente": False},
        {"id": "con-042", "texto": "Cerrar puertas y ventanas de los ambientes comunes cuando la calefacción está encendida. Cerrar cortinas y persianas por la noche.", "urgente": False},
        {"id": "con-043", "texto": "Para ventilar espacios comunes, es suficiente abrir ventanas entre 5 a 10 minutos para renovar el aire.", "urgente": False},
        {"id": "con-044", "texto": "Limpiar y hacer mantenimiento de sistemas de calefacción (calderas y calefactores) para reducir el consumo y extender su vida útil.", "urgente": False},
        {"id": "con-045", "texto": "No cubrir ni colocar objetos al lado de los radiadores, ya que dificulta la emisión de aire caliente.", "urgente": False},
        {"id": "con-046", "texto": "Verificar anualmente que los radiadores no tengan aire en su interior, ya que dificulta la transmisión de calor.", "urgente": False},
        {"id": "con-047", "texto": "Asegurar un buen mantenimiento y aislamiento de acumuladores y tuberías de distribución de agua caliente para eliminar pérdidas.", "urgente": False},
        {"id": "con-048", "texto": "Es preferible bajar la temperatura de los equipos que generan ACS antes que recurrir a la mezcla de agua caliente y fría.", "urgente": False},
        {"id": "con-049", "texto": "Colocar burletes en puertas y ventanas para reducir las infiltraciones de aire en los espacios comunes calefaccionados.", "urgente": False},
        {"id": "con-050", "texto": "Realizar una revisión anual de la caldera/generador de calor, incluyendo el quemador, gases de escape y limpieza del sistema.", "urgente": False},
        {"id": "con-051", "texto": "Chequear que la calidad del agua sea adecuada para evitar incrustaciones de sarro y deposición de óxido; considerar un sistema de tratamiento de agua.", "urgente": False},
        {"id": "con-052", "texto": "Reubicar termostatos alejados de fuentes de calor y frío, e instalarlos en las salas más utilizadas a 1.5m de altura.", "urgente": False},
        {"id": "con-053", "texto": "En calderas, regular el caudal de agua con válvulas para ajustarlo a las necesidades reales de calefacción.", "urgente": False},
        {"id": "con-054", "texto": "Utilizar artefactos sin llama piloto permanente para sistemas de producción instantánea o de acumulación.", "urgente": False},
        {"id": "con-055", "texto": "Considerar la instalación de calderas más eficientes (baja temperatura o condensación) frente a grandes mantenimientos o recambios.", "urgente": False},
        {"id": "con-056", "texto": "En calderas grandes, instalar un termómetro en la chimenea para detectar variaciones de temperatura en gases de escape.", "urgente": False},
        {"id": "con-057", "texto": "Mejorar el aislamiento térmico de la envolvente del edificio (muros, cubiertas, suelos, tabiques, huecos) para reducir la demanda de calefacción y refrigeración.", "urgente": True if consumo_actual > 350 else False},
        {"id": "con-058", "texto": "Aislar todas las tuberías que pasen por espacios no calefaccionados (sala de calderas, garajes, falsos techos) para evitar pérdidas de calor.", "urgente": False},
        {"id": "con-059", "texto": "Considerar aislar terrazas o techos, y viviendas que descansan sobre espacios abiertos, sótanos o garajes.", "urgente": False},
        {"id": "con-060", "texto": "Considerar la incorporación de techos verdes o jardines verticales para mejorar la climatización del edificio.", "urgente": False},
        {"id": "con-061", "texto": "Establecer un programa de detección periódica de humedad, incluyendo la revisión de goteras y tuberías rotas.", "urgente": False},
        {"id": "con-062", "texto": "Asegurar un buen diseño en zonas con cambios de espesor o uniones de distintos materiales en la envolvente del edificio para evitar puentes térmicos.", "urgente": False},
        {"id": "con-063", "texto": "Revisar periódicamente puertas y ventanas para evitar pérdidas por infiltración debido a mal estado.", "urgente": False},
        {"id": "con-064", "texto": "Considerar la renovación de vidrios y marcos, y la utilización de Doble Vidriado Hermético (DVH) para mejorar la eficiencia y confort.", "urgente": False},
        {"id": "con-065", "texto": "Incluir persianas o cortinas en aberturas para proteger superficies vidriadas en invierno, y aleros o toldos en aberturas orientadas al norte en verano.", "urgente": False},
        {"id": "con-066", "texto": "Utilizar luminarias más eficientes y sistemas automáticos como sensores de presencia, e integrar luz natural en garajes para reducir el consumo de iluminación.", "urgente": False},
        {"id": "con-067", "texto": "Utilizar Tragaluze Tubulares o Tubos Solares para iluminación natural en interiores sin aumentar cargas térmicas.", "urgente": False},
        {"id": "con-068", "texto": "Realizar un adecuado mantenimiento preventivo en instalaciones de garajes para mejorar el rendimiento y reducir costos.", "urgente": False},
        {"id": "con-069", "texto": "Al accionar accesos automáticos de garajes, considerar sistemas de bajo rozamiento, motores de alta eficiencia y arrancadores suaves para grandes accesos.", "urgente": False},
        {"id": "con-070", "texto": "Apagar las luces que no se utilizan en espacios de uso común.", "urgente": False},
        {"id": "con-071", "texto": "Eliminar las pérdidas de agua en espacios de uso común.", "urgente": False},
        {"id": "con-072", "texto": "Apagar la calefacción en los espacios de uso común que no se utilizan.", "urgente": False},
        {"id": "con-073", "texto": "Ajustar la temperatura del aire acondicionado a 24°C en verano; bajarla más es un gasto innecesario.", "urgente": True if consumo_actual > 250 else False},
        {"id": "con-074", "texto": "Ajustar la temperatura de calefacción a 20°C en invierno para mantener un ambiente confortable.", "urgente": False},
        {"id": "con-075", "texto": "Utilizar la posición de ventilación en aires acondicionados para ahorrar energía.", "urgente": False},
        {"id": "con-076", "texto": "Considerar sistemas evaporativos para refrescar el ambiente; su consumo es muy bajo.", "urgente": False},
        {"id": "con-077", "texto": "En determinados lugares, un ventilador (preferentemente de techo) puede ser suficiente para el confort, produciendo una sensación de descenso de temperatura de 3 a 5°C.", "urgente": False},
        {"id": "con-078", "texto": "Limpiar los filtros de los aires acondicionados cada temporada.", "urgente": False},
        {"id": "con-079", "texto": "Al actualizar o realizar grandes mantenimientos en sistemas de climatización, evaluar un recambio por tecnología de mayor eficiencia.", "urgente": False},
        {"id": "con-080", "texto": "Instalar toldos, aleros o persianas en ventanas con exposición al sol para reducir la ganancia térmica y el uso de aire acondicionado.", "urgente": False},
    ]
    
    # Filtrar consejos ya cumplidos
    consejos_filtrados = [c for c in all_consejos if c["id"] not in consejos_cumplidos_ids]
    
    # Asegurarse de que al menos un consejo urgente aparezca si hay alguno disponible
    if any(c.get("urgente", False) for c in consejos_filtrados):
        urgentes_disponibles = [c for c in consejos_filtrados if c.get("urgente", False)]
        
        consejos_final = []
        if urgentes_disponibles:
            consejos_final.append(random.choice(urgentes_disponibles))

            consejos_filtrados = [c for c in consejos_filtrados if c["id"] != consejos_final[0]["id"]]
        
        random.shuffle(consejos_filtrados)
        consejos_final.extend(consejos_filtrados[:min(len(consejos_filtrados), 4)]) # Add up to 4 more tips
    else:

        random.shuffle(consejos_filtrados)
        consejos_final = consejos_filtrados[:min(len(consejos_filtrados), 5)]


    for c in all_consejos:
        c["cumplido"] = c["id"] in consejos_cumplidos_ids

    return all_consejos

# - ENDPOINTS DE LA API -

# - Autenticación y Perfil -
@app.post("/login")
async def login(peticion: PeticionLogin):
    # Buscar usuario por email
    response = supabase.table('usuarios').select("*").eq('email', peticion.username).execute()
    
    if not response.data:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    usuario = response.data[0]
    
    if usuario['password'] == peticion.password:  # En producción usa verificación de hash
        return {
            "mensaje": "Inicio de sesión exitoso", 
            "usuario_id": usuario['id'],
            "email": usuario['email'],
            "nombre": usuario['nombre']
        }
    
    raise HTTPException(status_code=401, detail="Credenciales incorrectas")
@app.post("/registro")
async def registro(peticion: PeticionRegistro):
    # Verificar si el email ya existe
    response = supabase.table('usuarios').select("id").eq('email', peticion.email).execute()
    
    if response.data:
        raise HTTPException(status_code=409, detail="El usuario ya existe")
    
    # Crear nuevo usuario
    nuevo_usuario = {
        "email": peticion.email,
        "password": peticion.password,  # En producción deberías hashear esto
        "nombre": peticion.nombre,
        "ubicacion": peticion.ubicacion,
        "nivel_subsidio": peticion.nivel_subsidio,
        "personas": peticion.personas,
        "lat": peticion.lat,
        "lon": peticion.lon,
        "puntos_sostenibilidad": 0
    }
    
    response = supabase.table('usuarios').insert(nuevo_usuario).execute()
    
    return {
        "mensaje": "Usuario registrado correctamente", 
        "usuario_id": response.data[0]['id']
    }
@app.get("/usuarios/{usuario_id}")
async def obtener_perfil_usuario(usuario_id: str):
    response = supabase.table('usuarios').select(
        "id", "email", "nombre", "ubicacion", "lat", "lon", 
        "personas", "creado_en", "nivel_subsidio", "puntos_sostenibilidad"
    ).eq('id', usuario_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return response.data[0]

@app.put("/usuarios/{usuario_id}")
async def actualizar_perfil_usuario(usuario_id: str, datos_actualizados: Dict):
    campos_permitidos = {
        "nombre", "ubicacion", "lat", "lon", 
        "personas", "nivel_subsidio", "password"
    }
    
    # Filtrar solo campos permitidos
    updates = {k: v for k, v in datos_actualizados.items() if k in campos_permitidos}
    
    if not updates:
        raise HTTPException(status_code=400, detail="No se proporcionaron campos válidos para actualizar")
    
    response = supabase.table('usuarios').update(updates).eq('id', usuario_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"mensaje": "Perfil actualizado correctamente"}
# --- Facturas ---
# Endpoint para obtener facturas
@app.get("/facturas/{usuario_id}")
async def obtener_facturas(usuario_id: str):
    try:
        facturas = cargar_datos_facturas(usuario_id)
        if facturas is None:
            raise HTTPException(status_code=404, detail="Error al cargar facturas")
        return facturas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    


@app.post("/facturas/{usuario_id}", summary="Añadir una nueva factura para un usuario.")
async def anadir_factura(usuario_id: str, factura_data: dict):
    supabase = get_supabase_client()
    try:
        # Validar datos primero
        if not all(key in factura_data for key in ['mes', 'anio', 'consumo_kwh', 'costo']):
            raise HTTPException(status_code=400, detail="Datos de factura incompletos")
        
        # Insertar en Supabase
        response = supabase.table("facturas").insert({
            "usuario_id": usuario_id,
            **factura_data
        }).execute()
        
        return {"mensaje": "Factura creada", "id": response.data[0]['id']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/facturas/{usuario_id}/{factura_id}", summary="Eliminar una factura de un usuario.")
async def eliminar_factura(usuario_id: str, factura_id: str):
    try:
        # Verificar que la factura pertenece al usuario
        factura_response = supabase.table('facturas').select("id").eq('id', factura_id).eq('usuario_id', usuario_id).execute()
        if not factura_response.data:
            raise HTTPException(status_code=404, detail="Factura no encontrada para el usuario")

        # Eliminar factura
        supabase.table('facturas').delete().eq('id', factura_id).execute()
        return {"mensaje": "Factura eliminada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar factura: {str(e)}")
    
    
    
# --- Electrodomésticos ---
@app.get("/electrodomesticos/{usuario_id}")
async def obtener_electrodomesticos(usuario_id: str):
    try:
        electrodomesticos = cargar_datos_electrodomesticos(usuario_id)
        if electrodomesticos is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return electrodomesticos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
@app.post("/electrodomesticos/{usuario_id}", summary="Añadir un nuevo electrodoméstico a un usuario.")
async def anadir_electrodomestico(usuario_id: str, electrodomestico: Electrodomestico):
    try:
        # Verificar que el usuario existe
        user_response = supabase.table('usuarios').select("id").eq('id', usuario_id).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Insertar electrodoméstico
        electrodomestico_data = {
            "usuario_id": usuario_id,
            "nombre": electrodomestico.nombre,
            "cantidad": electrodomestico.cantidad,
            "potencia": electrodomestico.potencia,
            "eficiencia": electrodomestico.eficiencia,
            "horas_dia": electrodomestico.horas_dia,
            "dias_mes": electrodomestico.dias_mes
        }
        
        response = supabase.table('electrodomesticos').insert(electrodomestico_data).execute()
        return {"mensaje": "Electrodoméstico añadido correctamente", "electrodomestico_id": response.data[0]['id']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al añadir electrodoméstico: {str(e)}")
    
    
    
@app.put("/electrodomesticos/{usuario_id}/{electrodomestico_id}", summary="Actualizar un electrodoméstico de un usuario.")
async def actualizar_electrodomestico(usuario_id: str, electrodomestico_id: str, datos_actualizados: Dict):
    try:
        # Verificar que el electrodoméstico pertenece al usuario
        ed_response = supabase.table('electrodomesticos').select("id").eq('id', electrodomestico_id).eq('usuario_id', usuario_id).execute()
        if not ed_response.data:
            raise HTTPException(status_code=404, detail="Electrodoméstico no encontrado para el usuario")

        # Actualizar electrodoméstico
        supabase.table('electrodomesticos').update(datos_actualizados).eq('id', electrodomestico_id).execute()
        return {"mensaje": "Electrodoméstico actualizado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar electrodoméstico: {str(e)}")
    
    
    
    
@app.delete("/electrodomesticos/{usuario_id}/{electrodomestico_id}", summary="Eliminar un electrodoméstico de un usuario.")
async def eliminar_electrodomestico(usuario_id: str, electrodomestico_id: str):
    try:
        # Verificar que el electrodoméstico pertenece al usuario
        ed_response = supabase.table('electrodomesticos').select("id").eq('id', electrodomestico_id).eq('usuario_id', usuario_id).execute()
        if not ed_response.data:
            raise HTTPException(status_code=404, detail="Electrodoméstico no encontrado para el usuario")

        # Eliminar electrodoméstico
        supabase.table('electrodomesticos').delete().eq('id', electrodomestico_id).execute()
        return {"mensaje": "Electrodoméstico eliminado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar electrodoméstico: {str(e)}")
    
    
    
@app.get("/catalogo/electrodomesticos", summary="Obtener el catálogo de electrodomésticos.")
async def obtener_catalogo_electrodomesticos():
    return BASE_ELECTRODOMESTICOS

# - Cálculos -
@app.post("/calcular/costo", summary="Calcular costo estimado basado en kWh y subsidio.")
async def calcular_costo_endpoint(peticion: CalculoKWH):
    user_location = "Resistencia, Chaco"
    found_user = None
    for user_data_val in db_usuarios.values():
        if user_data_val["nivel_subsidio"] == peticion.nivel_subsidio:
            found_user = user_data_val
            user_location = found_user["ubicacion"]
            break
            
    costo_calculado = calcular_costo_rango(peticion.kwh, peticion.nivel_subsidio, user_location)
    return {"costo_estimado": costo_calculado}

@app.post("/calcular/huella_carbono", summary="Calcular huella de carbono basada en kWh.")
async def calcular_huella_carbono_endpoint(peticion: CalculoKWH):
    huella_calculada = calcular_huella_carbono(peticion.kwh)
    return {"huella_carbono_kg_co2": huella_calculada}

# - Consejos -
@app.get("/consejos/{usuario_id}", summary="Obtener consejos de sostenibilidad para un usuario.")
async def obtener_consejos(usuario_id: str):
    user_data = None
    for u_data in db_usuarios.values():
        if u_data["id"] == usuario_id:
            user_data = u_data
            break

    if user_data:
        consumo_simulado = sum(f["consumo_kwh"] for f in user_data["facturas"]) if user_data["facturas"] else 0
        huella_simulada = calcular_huella_carbono(consumo_simulado)
        
        consejos_generados = generar_consejos_dinamicos(
            consumo_simulado,
            huella_simulada,
            user_data["puntos_sostenibilidad"],
            user_data["consejos_cumplidos"]
        )
        return {"consejos": consejos_generados, "puntos_sostenibilidad": user_data["puntos_sostenibilidad"]}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.post("/consejos/{username}/marcar_cumplido", summary="Marcar un consejo como cumplido y sumar puntos.")
async def marcar_consejo_cumplido(username: str, peticion: MarcarConsejoCumplido):
    user_data = db_usuarios.get(username)
    if user_data:
        consejo_id = peticion.consejo_id
        if consejo_id not in user_data["consejos_cumplidos"]:
            db_usuarios[username]["consejos_cumplidos"].append(consejo_id)
            db_usuarios[username]["puntos_sostenibilidad"] += 10
            
            hoy = datetime.now().strftime("%Y-%m-%d")
            if user_data["progreso_sostenibilidad"] and user_data["progreso_sostenibilidad"][-1]["fecha"] == hoy:
                db_usuarios[username]["progreso_sostenibilidad"][-1]["puntos"] = db_usuarios[username]["puntos_sostenibilidad"]
            else:
                db_usuarios[username]["progreso_sostenibilidad"].append({"fecha": hoy, "puntos": db_usuarios[username]["puntos_sostenibilidad"]})
            
            return {"mensaje": "Consejo marcado como cumplido y puntos añadidos", "puntos_actuales": db_usuarios[username]["puntos_sostenibilidad"]}
        return {"mensaje": "Consejo ya estaba marcado como cumplido"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

# - Nuevos Endpoints para Métricas y Resumen -
@app.get("/metricas/resumen/{usuario_id}", summary="Obtener métricas de resumen principales para la página de Inicio.")
async def obtener_metricas_resumen(usuario_id: str):
    user_data = None
    for u_data in db_usuarios.values():
        if u_data["id"] == usuario_id:
            user_data = u_data
            break

    if user_data:
        total_consumo_kwh = sum(f["consumo_kwh"] for f in user_data["facturas"]) if user_data["facturas"] else 0
        total_costo = sum(f["costo"] for f in user_data["facturas"]) if user_data["facturas"] else 0
        total_huella_co2 = calcular_huella_carbono(total_consumo_kwh)
        puntos_sostenibilidad = user_data["puntos_sostenibilidad"]

        desglose_electrodomesticos = []
        for ed in user_data["electrodomesticos"]:
            consumo_activo_ed = (ed["potencia"] / 1000) * ed["horas_dia"] * ed["dias_mes"] * ed["cantidad"]
            total_kwh_ed = consumo_activo_ed
            desglose_electrodomesticos.append({
                "nombre": ed["nombre"],
                "total_kwh": round(total_kwh_ed, 2)
            })
        
        consejos_disponibles = generar_consejos_dinamicos(total_consumo_kwh, total_huella_co2, puntos_sostenibilidad, user_data["consejos_cumplidos"])
        consejos_no_cumplidos = [c for c in consejos_disponibles if not c.get("cumplido")]
        consejo_dinamico = random.choice(consejos_no_cumplidos) if consejos_no_cumplidos else {"id": "con-000", "texto": "¡Bienvenido a BioTrack! Comienza a registrar tus facturas y electrodomésticos.", "urgente": False}

        return {
            "consumo_total_kwh": total_consumo_kwh,
            "costo_total": total_costo,
            "huella_co2_total": total_huella_co2,
            "puntos_sostenibilidad": puntos_sostenibilidad,
            "consejo_dinamico": consejo_dinamico,
            "desglose_electrodomesticos": desglose_electrodomesticos,
            "resumen_actividad": {
                "facturas_consumo": total_consumo_kwh,
                "facturas_costo": total_costo,
                "estimado_consumo": sum(item["total_kwh"] for item in desglose_electrodomesticos),
                "estimado_costo": calcular_costo_rango(sum(item["total_kwh"] for item in desglose_electrodomesticos), user_data["nivel_subsidio"], user_data["ubicacion"])
            }
        }
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.get("/metricas/perfil/{usuario_id}", summary="Obtener métricas y progreso para la página de Perfil.")
async def obtener_metricas_perfil(usuario_id: str):
    user_data = None
    for u_data in db_usuarios.values():
        if u_data["id"] == usuario_id:
            user_data = u_data
            break

    if user_data:
        emisiones_sesion_simuladas = random.uniform(0.1, 5.0)
        energia_sesion_simulada = random.uniform(0.1, 15.0)

        total_consumo_facturas = sum(f["consumo_kwh"] for f in user_data["facturas"]) if user_data["facturas"] else 0
        total_costo_facturas = sum(f["costo"] for f in user_data["facturas"]) if user_data["facturas"] else 0

        df_electrodomesticos = pd.DataFrame(user_data["electrodomesticos"])
        total_consumo_estimado = 0
        total_costo_estimado = 0
        if not df_electrodomesticos.empty:
            df_electrodomesticos["total_kwh"] = (df_electrodomesticos["potencia"] * df_electrodomesticos["horas_dia"] * df_electrodomesticos["dias_mes"] * df_electrodomesticos["cantidad"]) / 1000
            total_consumo_estimado = df_electrodomesticos["total_kwh"].sum()
            total_costo_estimado = calcular_costo_rango(total_consumo_estimado, user_data["nivel_subsidio"], user_data["ubicacion"])
        
        return {
            "puntos_sostenibilidad": user_data["puntos_sostenibilidad"],
            "consejos_cumplidos_count": len(user_data["consejos_cumplidos"]),
            "emisiones_sesion_kg_co2": emisiones_sesion_simuladas,
            "energia_sesion_kwh": energia_sesion_simulada,
            "progreso_sostenibilidad": user_data["progreso_sostenibilidad"],
            "resumen_actividad": {
                "facturas_consumo": total_consumo_facturas,
                "facturas_costo": total_costo_facturas,
                "estimado_consumo": total_consumo_estimado,
                "estimado_costo": total_costo_estimado
            },
            "nombre": user_data.get("nombre", "N/A"),
            "username": user_data.get("username", "N/A"),
            "ubicacion": user_data.get("ubicacion", "N/A"),
            "nivel_subsidio": user_data.get("nivel_subsidio", "N/A"),
        }
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.post("/generar_datos_prueba/{usuario_id}", summary="Generar datos de prueba para un usuario.")
async def generar_datos_prueba(usuario_id: str):
    try:
        # Verificar que el usuario existe
        user_response = supabase.table('usuarios').select("id").eq('id', usuario_id).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Generar facturas de prueba
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        user_data = user_response.data[0]
        facturas_prueba = []
        
        for i in range(6):  # Últimos 6 meses
            consumo_kwh = random.uniform(100, 400)
            costo = calcular_costo_rango(consumo_kwh, user_data["nivel_subsidio"], user_data["ubicacion"])
            
            factura_data = {
                "usuario_id": usuario_id,
                "mes": meses[i],
                "anio": datetime.now().year,
                "consumo_kwh": round(consumo_kwh, 2),
                "costo": round(costo, 2)
            }
            facturas_prueba.append(factura_data)
        
        # Insertar facturas de prueba
        supabase.table('facturas').insert(facturas_prueba).execute()

        # Generar electrodomésticos de prueba
        electrodomesticos_prueba = []
        for item in random.sample(BASE_ELECTRODOMESTICOS, k=min(5, len(BASE_ELECTRODOMESTICOS))):
            cantidad = random.randint(1, 2)
            horas_dia = item.get("horas_dia_estandar", random.uniform(1, 10))
            dias_mes = item.get("dias_mes_estandar", random.randint(15, 30))
            potencia_w = item.get("potencia_base", 0.0)
            
            electrodomestico_data = {
                "usuario_id": usuario_id,
                "nombre": item["nombre"],
                "cantidad": cantidad,
                "potencia": potencia_w,
                "eficiencia": item["eficiencia_estandar"],
                "horas_dia": round(horas_dia, 1),
                "dias_mes": dias_mes
            }
            electrodomesticos_prueba.append(electrodomestico_data)
        
        # Insertar electrodomésticos de prueba
        supabase.table('electrodomesticos').insert(electrodomesticos_prueba).execute()

        return {"mensaje": "Datos de prueba generados exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar datos de prueba: {str(e)}")