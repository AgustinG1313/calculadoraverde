"""
Página de Consejos. Muestra recomendaciones de sostenibilidad.
"""
import streamlit as st
import requests
import plotly.graph_objects as go
from services import api_client
from services.api_client import URL_API

def obtener_icono_consejo(texto_consejo):
    """Asigna un icono basado en palabras clave."""
    texto = texto_consejo.lower()
    if "luz" in texto or "led" in texto: return "💡"
    if "agua" in texto or "ducha" in texto: return "💧"
    if "acondicionado" in texto or "temperatura" in texto: return "🌡️"
    if "electrodoméstico" in texto or "desconecta" in texto: return "🔌"
    return "🌱"

def marcar_y_refrescar(username, consejo_id):
    """Callback para marcar un consejo y refrescar la data."""
    res = api_client.marcar_consejo_cumplido(username, consejo_id)
    if res:
        st.toast("¡+10 Puntos de Sostenibilidad!", icon="🎉")
        st.cache_data.clear()

def mostrar_consejos(estado_app):
    st.title("Consejos de Sostenibilidad")

    # --- Panel de Impacto Energético Promedio (Gauges) ---
    st.markdown("<p class='titleSection'>Tu Impacto Energético Promedio</p>", unsafe_allow_html=True)
    metricas_perfil = api_client.cargar_metricas_perfil(estado_app.usuario_actual_id)
    
    facturas = api_client.cargar_datos_facturas(estado_app.usuario_actual)
    if metricas_perfil and facturas:
        num_facturas = len(facturas)
        consumo_promedio = metricas_perfil["resumen_actividad"]["facturas_consumo"] / num_facturas
        
        huella_promedio_res = requests.post(f"{URL_API}/calcular/huella_carbono", json={"kwh": consumo_promedio, "nivel_subsidio": "medio"}).json()
        huella_promedio = huella_promedio_res.get("huella_carbono_kg_co2", 0)

        col1, col2 = st.columns(2)
        with col1:
            fig_consumo = go.Figure(go.Indicator(
                mode="gauge+number", value=consumo_promedio,
                title={'text': "Consumo Mensual Promedio (kWh)"},
                gauge={'axis': {'range': [0, 500]}, 'bar': {'color': "#81C784"},
                       'steps': [{'range': [0, 150], 'color': "#E8F5E9"}, {'range': [150, 300], 'color': "#A5D6A7"}]}))
            st.plotly_chart(fig_consumo, use_container_width=True)
        with col2:
            fig_huella = go.Figure(go.Indicator(
                mode="gauge+number", value=huella_promedio,
                title={'text': "Huella CO₂ Mensual Promedio (kg)"},
                gauge={'axis': {'range': [0, 150]}, 'bar': {'color': "#64B5F6"},
                       'steps': [{'range': [0, 45], 'color': "#E3F2FD"}, {'range': [45, 90], 'color': "#BBDEFB"}]}))
            st.plotly_chart(fig_huella, use_container_width=True)
        
        arboles_equivalentes = huella_promedio / 21
        st.markdown(f"""
            <div class="trees-info-box">
                <span class="trees-info-icon">🌳</span>
                <div class="trees-info-content">
                    <strong>Tu huella de carbono mensual equivale a la absorción de {arboles_equivalentes:.2f} árboles.</strong>
                    <p>Cada pequeño cambio ayuda a reducir este número.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Registra al menos una factura para ver tu impacto promedio.")
    
    st.divider()

    # --- Lista de Consejos en Tarjetas (una sola columna, ancho completo) ---
    st.markdown("<p class='titleSection'>Consejos para ti</p>", unsafe_allow_html=True)
    consejos_data = api_client.cargar_consejos(estado_app.usuario_actual_id)
    if not consejos_data:
        st.info("No hay consejos disponibles en este momento.")
        return

    no_cumplidos = [c for c in consejos_data if not c.get("cumplido")]
    
    for consejo in no_cumplidos:
        # Usar st.container con borde para crear el marco de la tarjeta
        with st.container(border=True):
            # Columnas internas para alinear texto y botón
            text_col, btn_col = st.columns([0.8, 0.2])
            
            with text_col:
                # El estilo 'display: flex' ayuda a centrar verticalmente el texto
                st.markdown(f"<div style='display: flex; align-items: center; height: 100%; min-height: 40px;'>{consejo['texto']}</div>", unsafe_allow_html=True)
            
            with btn_col:
                if st.button("¡Hecho!", key=f"done_{consejo['id']}", use_container_width=True):
                    marcar_y_refrescar(estado_app.usuario_actual, consejo['id'])
                    st.rerun()

    with st.expander("✅ Ver consejos cumplidos"):
        cumplidos = [c for c in consejos_data if c.get("cumplido")]
        if cumplidos:
            for consejo in cumplidos:
                st.markdown(f"- ~~{consejo['texto']}~~")
        else:
            st.write("Aún no has completado ningún consejo.")
