"""
Página de Perfil de Usuario. Muestra y permite editar la información del usuario.
"""
import streamlit as st
import requests
from services import api_client
from services.api_client import URL_API

def mostrar_perfil(estado_app):
    st.title("Mi Perfil")

    datos_perfil = api_client.cargar_metricas_perfil(estado_app.usuario_actual_id)
    if not datos_perfil:
        st.error("No se pudo cargar la información del perfil.")
        return

    # --- Tarjetas de Información del Perfil ---
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="profile-info-card">
            <span class="profile-info-card-icon">👤</span>
            <div class="profile-info-card-content">
                <strong>Nombre</strong>
                <span>{datos_perfil.get('nombre', 'N/A')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="profile-info-card">
            <span class="profile-info-card-icon">📍</span>
            <div class="profile-info-card-content">
                <strong>Ubicación</strong>
                <span>{datos_perfil.get('ubicacion', 'N/A')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="profile-info-card">
            <span class="profile-info-card-icon">✉️</span>
            <div class="profile-info-card-content">
                <strong>Correo Electrónico</strong>
                <span>{datos_perfil.get('username', 'N/A')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        nivel_display = {
            "alto": "N1 (Altos Ingresos)",
            "medio": "N3 (Ingresos Medios)",
            "bajo": "N2 (Bajos Ingresos)"
        }.get(datos_perfil.get('nivel_subsidio', 'N/A'), 'N/A')
        
        st.markdown(f"""
        <div class="profile-info-card">
            <span class="profile-info-card-icon">💰</span>
            <div class="profile-info-card-content">
                <strong>Nivel de Subsidio</strong>
                <span>{nivel_display}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- Métricas de Impacto Sostenible ---
    st.markdown("<p class='titleSection'>Tu Impacto Sostenible</p>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Puntos de Sostenibilidad 🌱", datos_perfil.get("puntos_sostenibilidad", 0))
    m2.metric("Consejos Cumplidos ✅", datos_perfil.get("consejos_cumplidos_count", 0))
    m3.metric("Emisiones de esta Sesión (kg CO₂)", f"{datos_perfil.get('emisiones_sesion_kg_co2', 0):.2f}")


    # --- Formulario para editar perfil ---
    with st.expander("⚙️ Editar Perfil"):
        with st.form("form_edit_perfil"):
            nombre = st.text_input("Nombre", value=datos_perfil.get('nombre', ''))
            ubicacion = st.text_input("Ubicación", value=datos_perfil.get('ubicacion', ''))
            
            niveles_map = {"N1 (Altos Ingresos)": "alto", "N2 (Bajos Ingresos)": "bajo", "N3 (Ingresos Medios)": "medio"}
            niveles_display_list = list(niveles_map.keys())
            current_nivel_backend = datos_perfil.get('nivel_subsidio', 'medio')
            current_display_name = next((k for k, v in niveles_map.items() if v == current_nivel_backend), niveles_display_list[2])
            index_actual = niveles_display_list.index(current_display_name)
            
            nuevo_nivel_display = st.selectbox("Nivel de Subsidio", niveles_display_list, index=index_actual)

            password = st.text_input("Nueva Contraseña (dejar vacío para no cambiar)", type="password")

            if st.form_submit_button("Guardar Cambios", type="primary"):
                payload = {
                    "nombre": nombre,
                    "ubicacion": ubicacion,
                    "nivel_subsidio": niveles_map[nuevo_nivel_display]
                }
                if password:
                    payload["password"] = password

                try:
                    res = requests.put(f"{URL_API}/usuarios/{estado_app.usuario_actual_id}", json=payload)
                    res.raise_for_status()
                    st.success("Perfil actualizado.")
                    st.cache_data.clear()
                    st.rerun()
                except requests.RequestException as e:
                    st.error(f"Error al actualizar: {e}")

    # --- Acciones de Sesión y Pruebas ---
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state.estado = type(st.session_state.estado)() 
        st.cache_data.clear()
        st.rerun()

    if st.button("Generar Datos de Prueba (si no existen)", type="secondary"):
        try:
            res = requests.post(f"{URL_API}/generar_datos_prueba/{estado_app.usuario_actual}")
            res.raise_for_status()
            st.success(res.json().get("mensaje"))
            st.cache_data.clear()
            st.rerun()
        except requests.RequestException as e:
            st.error(f"Error al generar datos: {e}")
