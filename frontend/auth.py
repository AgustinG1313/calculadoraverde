"""
Página y lógica para el inicio de sesión y registro de usuarios.
"""
import streamlit as st
import requests
from services.api_client import URL_API

def mostrar_inicio_sesion(estado_app):
    st.markdown("<h1 class='main-title'>BioTrack</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Conectá con un consumo que cuida tu mundo.</p>", unsafe_allow_html=True)
    
    _, col_main, _ = st.columns([1, 1.5, 1])
    with col_main:
        tab_login, tab_register = st.tabs(["Iniciar Sesión", "Registrarse"])
        
        with tab_login:
            with st.form(key="login_form"):
                correo = st.text_input("Correo Electrónico", value="usuario1@example.com")
                contrasena = st.text_input("Contraseña", type="password", value="password123")
                if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                    try:
                        res = requests.post(f"{URL_API}/login", json={"username": correo, "password": contrasena})
                        res.raise_for_status()
                        datos = res.json()
                        estado_app.sesion_iniciada = True
                        estado_app.usuario_actual = correo
                        estado_app.usuario_actual_id = datos.get("usuario_id")
                        st.rerun()
                    except requests.RequestException:
                        st.error("Credenciales incorrectas o error del servidor.")
        
        with tab_register:
            with st.form(key="register_form"):
                nombre = st.text_input("Nombre Completo")
                correo_nuevo = st.text_input("Correo (será tu usuario)")
                pass_nueva = st.text_input("Contraseña", type="password")
                ubicacion = st.selectbox("Ubicación", ["Resistencia, Chaco", "Otra"])
                nivel_subsidio_map = {"N1 (Altos ingresos)": "alto", "N2 (Bajos ingresos)": "bajo", "N3 (Ingresos medios)": "medio"}
                nivel_subsidio_display = st.selectbox("Nivel de Subsidio", list(nivel_subsidio_map.keys()))
                
                if st.form_submit_button("Crear Cuenta", type="primary", use_container_width=True):
                    payload = {
                        "username": correo_nuevo, "password": pass_nueva, "nombre": nombre,
                        "ubicacion": ubicacion, "nivel_subsidio": nivel_subsidio_map[nivel_subsidio_display]
                    }
                    try:
                        res = requests.post(f"{URL_API}/registro", json=payload)
                        res.raise_for_status()
                        st.success("¡Cuenta creada! Por favor, inicia sesión.")
                    except requests.RequestException:
                        st.error("Error al registrar. El usuario ya podría existir.")