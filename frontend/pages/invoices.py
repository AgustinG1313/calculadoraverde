"""
Página de Facturas. Permite registrar, ver y analizar facturas.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from services import api_client
from components import dialogs
from services.api_client import get_supabase_client

def mostrar_facturas(estado_app):
    st.title("Análisis de Facturas")

    # --- Botones de acción ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Añadir Factura Manual", use_container_width=True):
            dialogs.dialogo_registrar_factura(estado_app)
    with col2:
        if st.button("⬆️ Subir Factura (OCR)", use_container_width=True):
            dialogs.dialogo_subir_ocr()

    facturas = api_client.cargar_datos_facturas(estado_app.usuario_actual_id)
    if facturas is None:
        st.error("Error al cargar facturas. Por favor intenta nuevamente.")
    elif not facturas:  # Lista vacía
        st.info("""
        Aún no has registrado facturas. ¡Añade una para empezar!
            
        *Ve a la sección 'Añadir Factura' o importa tus datos históricos*
        """)
        
    print(f"ID de usuario: {estado_app.usuario_actual_id}")  # Debe ser un UUID
    print(f"Tipo de ID: {type(estado_app.usuario_actual_id)}")
    if not facturas:
        st.info("Aún no has registrado facturas. ¡Añade una para empezar!")
        return
    
    df = pd.DataFrame(facturas)

    # --- Panel de Análisis de Consumo ---
    st.markdown("<p class='titleSection'>Panel de Análisis de Consumo</p>", unsafe_allow_html=True)
    
    lista_anios = sorted(df["anio"].unique(), reverse=True)
    anio_seleccionado = st.selectbox("Selecciona un año para analizar:", lista_anios)
    
    df_seleccionado = df[df["anio"] == anio_seleccionado].copy()
    
    total_kwh_anual = df_seleccionado["consumo_kwh"].sum()
    total_costo_anual = df_seleccionado["costo"].sum()
    
    m1, m2 = st.columns(2)
    m1.metric("Consumo Anual Total", f"{total_kwh_anual:.2f} kWh")
    m2.metric("Costo Anual Real", f"${total_costo_anual:,.2f}")

    # --- Gráfico de Análisis Mensual ---
    st.markdown("<p class='titleSection'>Análisis Mensual</p>", unsafe_allow_html=True)
    
    # Mapeo de meses en español a números para ordenar correctamente
    meses_a_numeros = {
        "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
        "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
    }
    df_seleccionado['mes_num'] = df_seleccionado['mes'].map(meses_a_numeros)
    df_grafico = df_seleccionado.sort_values('mes_num')
    
    tipo_grafico = st.selectbox("Tipo de visualización:", ["Barras", "Línea", "Área"])

    y_column = "consumo_kwh"
    title_text = "Consumo Mensual (kWh)"
    
    if tipo_grafico == "Barras":
        fig = px.bar(df_grafico, x="mes", y=y_column, title=title_text)
    elif tipo_grafico == "Línea":
        fig = px.line(df_grafico, x="mes", y=y_column, markers=True, title=title_text)
    else: # Área
        fig = px.area(df_grafico, x="mes", y=y_column, title=title_text)
    
    st.plotly_chart(fig, use_container_width=True)


    # --- Tabla de detalles ---
    with st.expander("Ver detalle y eliminar facturas"):
        for _, factura in df_grafico.iterrows():
            cols = st.columns([0.6, 0.2, 0.2])
            cols[0].write(f"{factura['mes']} {factura['anio']} - {factura['consumo_kwh']} kWh - ${factura['costo']:.2f}")
            if cols[2].button("🗑️", key=f"del_{factura['id']}", help="Eliminar factura"):
                try:
                    supabase = get_supabase_client()
                    response = supabase.table("facturas").delete().eq("id", factura["id"]).execute()
                    if response.error:
                        st.error(f"Error al eliminar: {response.error.message}")
                    else:
                        st.success("Factura eliminada.")
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error inesperado: {e}")