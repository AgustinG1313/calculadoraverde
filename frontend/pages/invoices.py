"""
Página de Facturas. Permite registrar, ver y analizar facturas.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from components import dialogs
from services.api_client import get_supabase_client
from services.api_client import cargar_datos_facturas

def mostrar_facturas(estado_app):
    st.title("Análisis de Facturas")

    # --- Botones de acción ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Añadir Factura Manual", use_container_width=True):
            dialogs.dialogo_registrar_factura(estado_app)
    with col2:
        if st.button("⬆️ Subir Factura (OCR)", use_container_width=True):
            dialogs.dialogo_subir_ocr(estado_app)

    facturas = cargar_datos_facturas(estado_app.usuario_actual_id)
    if facturas is None:
        st.error("Error al cargar facturas. Por favor intenta nuevamente.")
        return
    elif not facturas:  # Lista vacía
        st.info("""
        Aún no has registrado facturas. ¡Añade una para empezar!
            
        *Ve a la sección 'Añadir Factura' o importa tus datos históricos*
        """)
        return
        
    
    
    try:
        df = pd.DataFrame(facturas)
        
       
        
        # Buscar la columna de año (puede venir como 'anio', 'año' o 'year')
        year_col = next((col for col in ['anio', 'año', 'year'] if col in df.columns), None)
        
        if year_col is None:
            st.error("No se encontró la columna de año en los datos. Columnas disponibles: " + ", ".join(df.columns))
            return
            
        # Convertir a numérico y manejar posibles valores nulos/inválidos
        df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
        df = df.dropna(subset=[year_col])
        df[year_col] = df[year_col].astype(int)
        
        # Verificar que tenemos datos después de la limpieza
        if df.empty:
            st.warning("No hay datos válidos después de la limpieza")
            return
            
        lista_anios = sorted(df[year_col].unique(), reverse=True)
        
        # --- Panel de Análisis de Consumo ---
        st.markdown("<p class='titleSection'>Panel de Análisis de Consumo</p>", unsafe_allow_html=True)
        
        anio_seleccionado = st.selectbox("Selecciona un año para analizar:", lista_anios)
        df_seleccionado = df[df[year_col] == anio_seleccionado].copy()
        
        # Resto del código igual...
        total_kwh_anual = df_seleccionado["consumo_kwh"].sum()
        total_costo_anual = df_seleccionado["costo"].sum()
        
        m1, m2 = st.columns(2)
        m1.metric("Consumo Anual Total", f"{total_kwh_anual:.2f} kWh")
        m2.metric("Costo Anual Real", f"${total_costo_anual:,.2f}")

        # --- Gráfico de Análisis Mensual ---
        st.markdown("<p class='titleSection'>Análisis Mensual</p>", unsafe_allow_html=True)
        
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
                cols[0].write(f"{factura['mes']} {factura[year_col]} - {factura['consumo_kwh']} kWh - ${factura['costo']:.2f}")
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
                        
    except Exception as e:
        st.error(f"Error al procesar los datos: {str(e)}")