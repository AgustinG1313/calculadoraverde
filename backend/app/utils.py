"""
Contiene funciones auxiliares y de lógica de negocio, como cálculos
de costos, huella de carbono y generación de consejos.
"""
import random
import functools
from datetime import datetime
from typing import List, Dict
from supabase import create_client, Client

SUPABASE_URL = "https://qhnkkybzcgjbjdepdewc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFobmtreWJ6Y2dqYmpkZXBkZXdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMwOTI2ODIsImV4cCI6MjA2ODY2ODY4Mn0.2p-yyHnBsWDpGpGN-94F10P-Wzn0H_ej5xSSXcb10NQ"

@functools.lru_cache(maxsize=128)
def calcular_costo_rango(kwh: float, nivel_subsidio: str, ubicacion: str = "Resistencia, Chaco") -> float:
    """Calcula el costo estimado de la factura eléctrica."""
    cargo_fijo = 2277.3100
    costo_total_kwh = 0.0

    tarifas_urbanas_n1 = [(50, 118.6888), (100, 126.6517), (150, 151.4252), (float('inf'), 163.8120)]
    tarifas_urbanas_n2 = [(50, 52.0293), (100, 59.9922), (150, 84.7657), (50, 97.1525), (float('inf'), 163.8120)]
    tarifas_urbanas_n3 = [(50, 67.1414), (100, 75.1043), (100, 99.8778), (50, 151.4252), (float('inf'), 163.8120)]
    tarifas_rurales = {"alto": [(float('inf'), 147.4494)], "bajo": [(350, 81.7632), (float('inf'), 147.4494)], "medio": [(250, 96.6547), (float('inf'), 147.4494)]}

    if "Chaco" in ubicacion:
        current_month = datetime.now().month
        is_summer = current_month in [1, 2, 3, 12]
        
        applied_tiers = []
        if "Rural" in ubicacion:
            applied_tiers = tarifas_rurales.get(nivel_subsidio, [])
        else:
            if nivel_subsidio == "bajo": applied_tiers = tarifas_urbanas_n2
            elif nivel_subsidio == "medio": applied_tiers = tarifas_urbanas_n3
            else: applied_tiers = tarifas_urbanas_n1
        
        remaining_kwh = kwh
        for block_size, rate in applied_tiers:
            if remaining_kwh <= 0: break
            consumed_in_block = min(remaining_kwh, block_size) if block_size != float('inf') else remaining_kwh
            current_rate = rate
            if "Rural" not in ubicacion:
                if is_summer:
                    if kwh <= 300: current_rate *= (1 - 0.60)
                    elif kwh <= 450: current_rate *= (1 - 0.50)
                else:
                    if kwh <= 200: current_rate *= (1 - 0.60)
                    elif kwh <= 300: current_rate *= (1 - 0.50)
            costo_total_kwh += consumed_in_block * current_rate
            remaining_kwh -= consumed_in_block
            
        costo_final = costo_total_kwh + cargo_fijo
        if is_summer and nivel_subsidio in ["bajo", "medio"]:
            if kwh <= 600: costo_final *= (1 - 0.29)
            elif kwh <= 800: costo_final *= (1 - 0.22)
            elif kwh <= 1000: costo_final *= (1 - 0.15)
    else:
        tarifa_base_n1 = 106.879
        if nivel_subsidio == "bajo":
            limite_subsidio, bonificacion = 350, 0.6815
            if kwh <= limite_subsidio: costo_total_kwh = kwh * tarifa_base_n1 * (1 - bonificacion)
            else: costo_total_kwh = (limite_subsidio * tarifa_base_n1 * (1 - bonificacion)) + ((kwh - limite_subsidio) * tarifa_base_n1)
        elif nivel_subsidio == "medio":
            limite_subsidio, bonificacion = 250, 0.5270
            if kwh <= limite_subsidio: costo_total_kwh = kwh * tarifa_base_n1 * (1 - bonificacion)
            else: costo_total_kwh = (limite_subsidio * tarifa_base_n1 * (1 - bonificacion)) + ((kwh - limite_subsidio) * tarifa_base_n1)
        else:
            costo_total_kwh = kwh * tarifa_base_n1
        costo_final = costo_total_kwh * 1.21

    return round(costo_final, 2)


@functools.lru_cache(maxsize=128)
def calcular_huella_carbono(kwh: float) -> float:
    """Calcula la huella de carbono en kg de CO2."""
    factor_emision_co2 = 0.3
    return round(kwh * factor_emision_co2, 2)

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
        {"id": "con-015", "texto": "Utiliza colores claros en paredes y techos para aprovechar mejor la iluminación natural.", "urgente": False},
        {"id": "con-016", "texto": "Reduce al mínimo la iluminación decorativa, tanto interior como exterior.", "urgente": False},
        {"id": "con-017", "texto": "Mantén limpias las lámparas y pantallas para aumentar la luminosidad sin aumentar su potencia.", "urgente": False},
    ]

    for c in all_consejos:
        c["cumplido"] = c["id"] in consejos_cumplidos_ids

    return all_consejos

def obtener_datos_usuario(user_id: str):
    usuario_resp = supabase.table("usuarios").select("*").eq("id", user_id).single().execute()
    usuario = usuario_resp.data if usuario_resp.data else {}
    facturas_resp = supabase.table("facturas").select("*").eq("usuario_id", user_id).execute()
    facturas = facturas_resp.data if facturas_resp.data else []
    consejos_cumplidos_resp = supabase.table("consejos_cumplidos").select("consejo_id").eq("usuario_id", user_id).execute()
    consejos_cumplidos_ids = [c["consejo_id"] for c in consejos_cumplidos_resp.data] if consejos_cumplidos_resp.data else []

    consumo_actual = sum(f["consumo_kwh"] for f in facturas)
    huella = calcular_huella_carbono(consumo_actual)
    puntos = usuario.get("puntos_sostenibilidad", 0)
    consejos = generar_consejos_dinamicos(consumo_actual, huella, puntos, consejos_cumplidos_ids)

    return {
        "usuario": usuario,
        "facturas": facturas,
        "consumo_actual": consumo_actual,
        "huella": huella,
        "consejos": consejos
    }