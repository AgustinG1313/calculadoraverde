"""
Página de Electrodomésticos. Permite gestionar el inventario de aparatos.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from services import api_client
from components import dialogs

def mostrar_electrodomesticos(estado_app):
    st.title("Gestión de Electrodomésticos")

    # Validar que tenemos un usuario_id válido
    if not hasattr(estado_app, 'usuario_actual_id') or not estado_app.usuario_actual_id:
        st.error("No se pudo identificar al usuario")
        return

    catalogo = api_client.cargar_catalogo_electrodomesticos()
    if not catalogo:
        st.warning("No se pudo cargar el catálogo de electrodomésticos")
        return
    
    inventario = api_client.cargar_datos_electrodomesticos(estado_app.usuario_actual_id)
    
    st.markdown("<p class='titleSection'>Añadir desde Catálogo</p>", unsafe_allow_html=True)
    if catalogo:
        nombres_inventario = {item['nombre'] for item in inventario} if inventario else set()
        opciones_disponibles = [item['nombre'] for item in catalogo if item['nombre'] not in nombres_inventario]
        
        col_select, col_btn = st.columns([0.8, 0.2])
        with col_select:
            if opciones_disponibles:
                aparato_seleccionado = st.selectbox(
                    "Selecciona un electrodoméstico para añadir:", 
                    opciones_disponibles, 
                    label_visibility="collapsed"
                )
            else:
                st.info("¡Has añadido todos los electrodomésticos del catálogo!")
                aparato_seleccionado = None
        
        with col_btn:
            if aparato_seleccionado and st.button("Añadir", type="primary", use_container_width=True):
                datos_aparato = next(item for item in catalogo if item['nombre'] == aparato_seleccionado)
                dialogs.dialogo_configurar_electrodomestico(aparato_seleccionado, datos_aparato, estado_app)

    st.markdown("<p class='titleSection'>Mi Inventario</p>", unsafe_allow_html=True)
    
    if not inventario:
        st.info("Tu inventario está vacío. Añade electrodomésticos desde el catálogo.")
        return

    # --- Métricas del inventario ---
    df_inventario = pd.DataFrame(inventario)
    df_inventario["total_kwh"] = (df_inventario["potencia"] * df_inventario["horas_dia"] * df_inventario["dias_mes"] * df_inventario["cantidad"]) / 1000
    total_kwh_inventario = df_inventario["total_kwh"].sum()
    
    costo_estimado = 0
    huella_kg = 0
    
    perfil_usuario = api_client.cargar_metricas_perfil(estado_app.usuario_actual_id)
    if perfil_usuario and total_kwh_inventario > 0:
        nivel_subsidio = perfil_usuario.get("nivel_subsidio", "medio")
        costo_estimado = api_client.calcular_costo_rango(total_kwh_inventario, nivel_subsidio)
        huella_kg = api_client.calcular_huella_carbono(total_kwh_inventario)

    m1, m2, m3 = st.columns(3)
    m1.metric("Consumo Estimado", f"{total_kwh_inventario:.2f} kWh/mes")
    m2.metric("Costo Estimado", f"${costo_estimado:,.2f} ARS/mes")
    m3.metric("Huella CO₂", f"{huella_kg:.2f} kg CO₂")

    # --- Lista de electrodomésticos ---
    for _, aparato in df_inventario.iterrows():
        col_icon, col_info, col_actions = st.columns([0.1, 0.7, 0.2])
        
        with col_icon:
            st.markdown(f'<span class="appliance-item-icon">🔌</span>', unsafe_allow_html=True)
            
        with col_info:
            st.write(f"**{aparato['nombre']}** (x{aparato['cantidad']})")
        
        with col_actions:
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button("✏️", key=f"edit_{aparato['id']}", help="Editar", use_container_width=True):
                    dialogs.dialogo_editar_electrodomestico(aparato.to_dict(), estado_app)
            with action_col2:
                if st.button("🗑️", key=f"del_{aparato['id']}", help="Eliminar", use_container_width=True):
                    if api_client.eliminar_electrodomestico(aparato["id"]):
                        st.success("Electrodoméstico eliminado")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Error al eliminar")

    # --- Gráfico de distribución ---
    st.markdown("<p class='titleSection'>Distribución del Consumo Estimado</p>", unsafe_allow_html=True)
    if not df_inventario.empty and df_inventario["total_kwh"].sum() > 0:
        fig = px.pie(df_inventario, names="nombre", values="total_kwh", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)