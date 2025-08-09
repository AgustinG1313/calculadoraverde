from services.api_client import get_supabase_client
import streamlit as st

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
                    supabase = get_supabase_client()
                    res = supabase.table("usuarios").select("*").eq("email", correo).single().execute()
                    usuario = res.data
                    if usuario and usuario["password"] == contrasena:
                        estado_app.sesion_iniciada = True
                        estado_app.usuario_actual = correo
                        estado_app.usuario_actual_id = usuario["id"]
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")

        with tab_register:
            with st.form(key="register_form"):
                nombre = st.text_input("Nombre Completo")
                correo_nuevo = st.text_input("Correo (será tu usuario)")
                pass_nueva = st.text_input("Contraseña", type="password")
                ubicacion = st.selectbox("Ubicación", ["Resistencia, Chaco", "Otra"])
                nivel_subsidio_map = {"N1 (Altos ingresos)": "alto", "N2 (Bajos ingresos)": "bajo", "N3 (Ingresos medios)": "medio"}
                nivel_subsidio_display = st.selectbox("Nivel de Subsidio", list(nivel_subsidio_map.keys()))
                
                if st.form_submit_button("Crear Cuenta", type="primary", use_container_width=True):
                    supabase = get_supabase_client()
                    payload = {
                        "email": correo_nuevo, 
                        "password": pass_nueva, 
                        "nombre": nombre,
                        "ubicacion": ubicacion, 
                        "nivel_subsidio": nivel_subsidio_map[nivel_subsidio_display],
                        "puntos_sostenibilidad": 0
                    }
                    try:
                        res = supabase.table("usuarios").insert(payload).execute()
                        if res.data:
                            st.success("¡Cuenta creada! Por favor, inicia sesión.")
                        else:
                            st.error("Error al registrar. El usuario ya podría existir.")
                    except Exception as e:
                        st.error(f"Error al registrar: {e}")