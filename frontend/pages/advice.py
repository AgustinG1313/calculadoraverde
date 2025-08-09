"""
Página de Consejos. Muestra recomendaciones de sostenibilidad.
"""
import streamlit as st
import plotly.graph_objects as go
from services import api_client

def mostrar_consejos(estado_app):
    st.title("🌱 Consejos de Sostenibilidad")
    
    # --- Validación inicial ---
    if not estado_app.usuario_actual_id:
        st.error("No se pudo identificar tu usuario. Por favor inicia sesión nuevamente.")
        return
    
    # --- Panel de Impacto Energético ---
    st.markdown("<p class='titleSection'>Tu Impacto Energético Promedio</p>", unsafe_allow_html=True)
    
    try:
        # Carga de datos con manejo de errores
        with st.spinner("Analizando tu consumo..."):
            metricas_perfil = api_client.cargar_metricas_perfil(estado_app.usuario_actual_id)
            facturas = api_client.cargar_datos_facturas(estado_app.usuario_actual_id)
            
            if metricas_perfil and facturas:
                
                pass
            else:
                st.info("""
                📌 **Registra al menos una factura para ver tu impacto**
                Ve a la sección *Facturas* y añade tu primer registro.
                """)
    except Exception as e:
        st.error(f"Error al calcular tu impacto energético: {str(e)}")

    st.divider()

    # --- Lista de Consejos ---
    st.markdown("<p class='titleSection'>Consejos Personalizados</p>", unsafe_allow_html=True)
    
    try:
        with st.spinner("Cargando tus consejos personalizados..."):
            consejos_data = api_client.cargar_consejos(estado_app.usuario_actual_id)
            
            if not consejos_data or len(consejos_data) == 0:
                st.info("""
                🎉 ¡Felicidades! Has completado todos los consejos disponibles.
                Pronto añadiremos más recomendaciones.
                """)
                return

            # Diccionario de íconos por categoría
            icons = {
                'ahorro': '💡',
                'agua': '💧',
                'climatización': '🌡️',
                'electricidad': '🔌',
                'general': '🌱'
            }

            # Consejos no cumplidos
            no_cumplidos = [c for c in consejos_data if not c.get("cumplido", False)]
            
            for consejo in no_cumplidos:
                with st.container(border=True):
                    cols = st.columns([0.8, 0.2])
                    
                    # Columna de contenido
                    with cols[0]:
                        categoria = consejo.get('categoria', 'general').lower()
                        icono = icons.get(categoria, '🌱')
                        
                        st.markdown(f"""
                            <div style='display: flex; align-items: center; min-height: 60px;'>
                                <span style='margin-right: 10px; font-size: 1.5em;'>{icono}</span>
                                <div>
                                    <div style='font-weight: bold;'>{consejo.get('titulo', 'Consejo práctico')}</div>
                                    <div style='color: #555; margin-top: 4px;'>{consejo['texto']}</div>
                                    <div style='font-size: 0.8em; color: #666; margin-top: 6px;'>
                                        Dificultad: {consejo.get('dificultad', 'media').capitalize()} • {consejo.get('puntos', 10)} puntos
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Columna del botón
                    with cols[1]:
                        if st.button("¡Hecho!", 
                                    key=f"done_{consejo['id']}",
                                    use_container_width=True,
                                    type="primary"):
                            if api_client.marcar_consejo_cumplido(estado_app.usuario_actual_id, consejo['id']):
                                st.toast(f"¡Consejo completado! +{consejo.get('puntos', 10)} puntos", icon="🎉")
                            else:
                                st.toast("Error al guardar", icon="⚠️")
                            st.rerun()

            # Consejos completados
            with st.expander("🏆 Mis logros completados", expanded=False):
                cumplidos = [c for c in consejos_data if c.get("cumplido", False)]
                
                if cumplidos:
                    for consejo in cumplidos:
                        st.markdown(f"""
                            <div style='display: flex; align-items: center; margin: 8px 0;'>
                                <span style='color: #4CAF50; margin-right: 8px;'>✓</span>
                                <span style='text-decoration: line-through; color: #777; flex-grow: 1;'>
                                    {consejo.get('titulo', 'Consejo completado')}
                                </span>
                                <span style='color: #4CAF50; font-weight: bold;'>
                                    +{consejo.get('puntos', 10)} pts
                                </span>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style='color: #666; text-align: center; margin: 20px 0;'>
                            Aún no has completado ningún consejo<br>
                            ¡Tu primer logro está a un click de distancia!
                        </div>
                    """, unsafe_allow_html=True)
                    
    except Exception as e:
        st.error(f"Error al cargar los consejos: {str(e)}")