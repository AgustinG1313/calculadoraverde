"""
Endpoints para obtener métricas consolidadas y generar datos de prueba.
"""
import random
import uuid
import pandas as pd
from fastapi import APIRouter, HTTPException
from ..database import db_usuarios, BASE_ELECTRODOMESTICOS
from ..utils import calcular_huella_carbono, calcular_costo_rango, generar_consejos_dinamicos

router = APIRouter(
    tags=["metricas"]
)

@router.get("/metricas/resumen/{usuario_id}", summary="Obtener métricas de resumen para la página de Inicio.")
async def obtener_metricas_resumen(usuario_id: str):
    user_data = next((u for u in db_usuarios.values() if u["id"] == usuario_id), None)
    if not user_data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    total_consumo = sum(f["consumo_kwh"] for f in user_data["facturas"])
    total_costo = sum(f["costo"] for f in user_data["facturas"])
    total_huella = calcular_huella_carbono(total_consumo)

    desglose = []
    for ed in user_data["electrodomesticos"]:
        consumo_ed = (ed["potencia"] / 1000) * ed["horas_dia"] * ed["dias_mes"] * ed["cantidad"]
        desglose.append({"nombre": ed["nombre"], "total_kwh": round(consumo_ed, 2)})

    consejos = generar_consejos_dinamicos(total_consumo, total_huella, user_data["puntos_sostenibilidad"], user_data["consejos_cumplidos"])
    no_cumplidos = [c for c in consejos if not c.get("cumplido")]
    consejo_dia = random.choice(no_cumplidos) if no_cumplidos else {"id": "con-000", "texto": "¡Bienvenido! Empieza a registrar tus datos.", "urgente": False}

    estimado_consumo = sum(item["total_kwh"] for item in desglose)
    estimado_costo = calcular_costo_rango(estimado_consumo, user_data["nivel_subsidio"], user_data["ubicacion"])

    return {
        "consumo_total_kwh": total_consumo,
        "costo_total": total_costo,
        "huella_co2_total": total_huella,
        "puntos_sostenibilidad": user_data["puntos_sostenibilidad"],
        "consejo_dinamico": consejo_dia,
        "desglose_electrodomesticos": desglose,
        "resumen_actividad": {
            "facturas_consumo": total_consumo,
            "facturas_costo": total_costo,
            "estimado_consumo": estimado_consumo,
            "estimado_costo": estimado_costo
        }
    }

@router.get("/metricas/perfil/{usuario_id}", summary="Obtener métricas para la página de Perfil.")
async def obtener_metricas_perfil(usuario_id: str):
    user_data = next((u for u in db_usuarios.values() if u["id"] == usuario_id), None)
    if not user_data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    total_consumo_facturas = sum(f["consumo_kwh"] for f in user_data["facturas"])
    total_costo_facturas = sum(f["costo"] for f in user_data["facturas"])

    df_electrodomesticos = pd.DataFrame(user_data["electrodomesticos"])
    total_consumo_estimado = 0
    if not df_electrodomesticos.empty:
        df_electrodomesticos["total_kwh"] = (df_electrodomesticos["potencia"] * df_electrodomesticos["horas_dia"] * df_electrodomesticos["dias_mes"] * df_electrodomesticos["cantidad"]) / 1000
        total_consumo_estimado = df_electrodomesticos["total_kwh"].sum()
    
    total_costo_estimado = calcular_costo_rango(total_consumo_estimado, user_data["nivel_subsidio"], user_data["ubicacion"])

    return {
        "puntos_sostenibilidad": user_data["puntos_sostenibilidad"],
        "consejos_cumplidos_count": len(user_data["consejos_cumplidos"]),
        "emisiones_sesion_kg_co2": random.uniform(0.1, 5.0),
        "energia_sesion_kwh": random.uniform(0.1, 15.0),
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

@router.post("/generar_datos_prueba/{username}", summary="Generar datos de prueba para un usuario.")
async def generar_datos_prueba(username: str):
    user_data = db_usuarios.get(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Generar facturas
    if not user_data["facturas"]:
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"]
        for mes in meses:
            consumo = random.uniform(100, 400)
            costo = calcular_costo_rango(consumo, user_data["nivel_subsidio"], user_data["ubicacion"])
            user_data["facturas"].append({
                "id": str(uuid.uuid4()), "mes": mes, "anio": 2024,
                "consumo_kwh": round(consumo, 2), "costo": round(costo, 2)
            })

    # Generar electrodomésticos
    if not user_data["electrodomesticos"]:
        for item in random.sample(BASE_ELECTRODOMESTICOS, k=min(5, len(BASE_ELECTRODOMESTICOS))):
            user_data["electrodomesticos"].append({
                "id": str(uuid.uuid4()), "nombre": item["nombre"],
                "cantidad": random.randint(1, 2), "potencia": item.get("potencia_base", 0.0),
                "eficiencia": item["eficiencia_estandar"],
                "horas_dia": item.get("horas_dia_estandar", 1.0),
                "dias_mes": item.get("dias_mes_estandar", 30)
            })
    
    return {"mensaje": "Datos de prueba generados exitosamente."}