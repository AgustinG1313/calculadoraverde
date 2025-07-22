# frontend/app.py

import streamlit as st
import os
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import uuid
from datetime import datetime
import random

# ---------- CONFIGURACIÓN INICIAL Y CARGA DE ESTILOS ----------
st.set_page_config(page_title="GreenCalc", page_icon="♻️", layout="wide")

def cargar_css(ruta_archivo):
    """Carga un archivo CSS para aplicar estilos personalizados."""
    try:
        with open(ruta_archivo, encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Archivo CSS no encontrado en la ruta: {ruta_archivo}")

# Obtener la ruta absoluta del archivo style.css
ruta_script = os.path.dirname(__file__)
ruta_css_absoluta = os.path.join(ruta_script, "style.css")
cargar_css(ruta_css_absoluta)

# ---------- CONSTANTES Y ESTADO DE LA APP ----------
st.cache_data(ttl=3600) # Cache para optimizar llamadas repetidas
URL_API = "http://127.0.0.1:8000" # URL de nuestro backend FastAPI

class EstadoApp:
    """Clase para gestionar el estado de la aplicación en st.session_state."""
    def __init__(self):
        self.sesion_iniciada = False
        self.usuario_actual = "" # Almacenará el username (correo electrónico)
        self.usuario_actual_id = None # Almacenará el ID de usuario (UUID)
        self.pagina_actual = "inicio_sesion"
        self.token = None # En una aplicación real, se usaría para autenticación
        # Estas variables se simularán o se obtendrán del backend si se implementa CodeCarbon
        self.emisiones_sesion = 0.0
        self.energia_sesion = 0.0
        self.modo_sostenible_activo = False
        self.puntos_sostenibilidad = 0
        self.consejos_cumplidos = []
        self.modo_administrador = False # Para el modo administrador

# Inicializar el estado de la aplicación si no existe en st.session_state
if "estado" not in st.session_state:
    st.session_state.estado = EstadoApp()
estado = st.session_state.estado


def cambiar_pagina(pagina):
    """Cambia la página actual de la aplicación."""
    estado.pagina_actual = pagina


# ---------- FUNCIONES DE DIÁLOGO (MODALES) ----------

@st.dialog("Subir Factura (OCR)")
def dialogo_subir_ocr():
    """Define la interfaz para el diálogo de subida de factura por OCR."""
    st.subheader("Sube tu factura para procesar")
    uploaded_file = st.file_uploader("Arrastra y suelta tu archivo aquí o haz clic para buscar", type=["pdf", "png", "jpg", "jpeg"], key="ocr_file_uploader")
    
    if uploaded_file is not None:
        st.info("Archivo recibido. La funcionalidad de procesamiento OCR está en desarrollo. ¡Gracias por tu paciencia!")
        # Here would be the logic to send the file to the backend for OCR
        # For now, we only show a message.

@st.dialog("Configurar Electrodoméstico")
def dialogo_configurar_electrodomestico(nombre_aparato, datos_aparato_catalogo):
    st.subheader(f"Añadir {nombre_aparato}")
    
    with st.form(key=f"form_electrodomestico_{nombre_aparato}"):
        col1, col2 = st.columns(2)
        with col1:
            cantidad = st.number_input("Cantidad", min_value=1, value=1, key=f"cant_{nombre_aparato}")
            potencia = st.number_input("Potencia (W)", min_value=0.0, value=float(datos_aparato_catalogo.get("potencia_base", 0)), key=f"pot_{nombre_aparato}")
        with col2:
            horas_dia = st.number_input("Horas de uso por día", min_value=0.0, max_value=24.0, value=float(datos_aparato_catalogo.get("horas_dia_estandar", 1.0)), step=0.5, key=f"hpd_{nombre_aparato}")
            dias_mes = st.number_input("Días de uso por mes", min_value=1, max_value=31, value=int(datos_aparato_catalogo.get("dias_mes_estandar", 30)), key=f"dpm_{nombre_aparato}")
        
        eficiencia = st.selectbox("Eficiencia Energética", ["A++", "A+", "A", "B", "C", "D", "E"], index=2, key=f"ef_{nombre_aparato}")

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            enviado = st.form_submit_button("Añadir al Inventario", type="primary", use_container_width=True)
        with col_cancel:
            if st.form_submit_button("Cancelar", use_container_width=True):
                st.session_state.dialog_open = False
                st.rerun()
        
        if enviado:
            if potencia <= 0 or horas_dia <= 0 or dias_mes <= 0:
                st.warning("Potencia, horas de uso y días al mes deben ser mayores a 0.")
            else:
                consumo_activo_kwh = (potencia * horas_dia * dias_mes * cantidad) / 1000
                
                payload = {
                    "id": str(uuid.uuid4()),
                    "nombre": nombre_aparato,
                    "cantidad": cantidad,
                    "potencia": potencia,
                    "eficiencia": eficiencia,
                    "horas_dia": horas_dia,
                    "dias_mes": dias_mes,
                    "consumo_kwh": round(consumo_activo_kwh, 2),
                    "total_kwh": round(consumo_activo_kwh, 2)
                }
                try:
                    respuesta = requests.post(f"{URL_API}/electrodomesticos/{estado.usuario_actual}", json=payload)
                    respuesta.raise_for_status()
                    st.success("Electrodoméstico añadido exitosamente.")
                    st.cache_data.clear()
                    st.session_state.dialog_open = False
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"No se pudo añadir el electrodoméstico: {e}")

@st.dialog("Editar Electrodoméstico")
def dialogo_editar_electrodomestico(aparato_existente):
    st.subheader(f"Editando ✏️ {aparato_existente['nombre']}")
    
    with st.form(key=f"form_edit_{aparato_existente['id']}"):
        col1, col2 = st.columns(2)
        with col1:
            cantidad = st.number_input("Cantidad", min_value=1, value=aparato_existente['cantidad'], key=f"edit_cant_{aparato_existente['id']}")
            potencia = st.number_input("Potencia (W)", min_value=0.0, value=float(aparato_existente['potencia']), key=f"edit_pot_{aparato_existente['id']}")
        with col2:
            horas_dia = st.number_input("Horas de uso por día", min_value=0.0, max_value=24.0, value=float(aparato_existente['horas_dia']), step=0.5, key=f"edit_hpd_{aparato_existente['id']}")
            dias_mes = st.number_input("Días de uso por mes", min_value=1, max_value=31, value=int(aparato_existente['dias_mes']), key=f"edit_dpm_{aparato_existente['id']}")
        
        eficiencia_options = ["A++", "A+", "A", "B", "C", "D", "E"]
        try:
            current_index = eficiencia_options.index(aparato_existente['eficiencia'])
        except ValueError:
            current_index = 2
        eficiencia = st.selectbox("Eficiencia Energética", eficiencia_options, index=current_index, key=f"edit_ef_{aparato_existente['id']}")
        
        col_submit, col_cancel = st.columns(2)
        with col_submit:
            enviado = st.form_submit_button("Guardar Cambios", type="primary", use_container_width=True)
        with col_cancel:
            if st.form_submit_button("Cancelar", use_container_width=True):
                st.session_state.dialog_open = False
                st.rerun()

        if enviado:
            if potencia <= 0 or horas_dia <= 0 or dias_mes <= 0:
                st.warning("Potencia, horas de uso y días al mes deben ser mayores a 0.")
            else:
                consumo_activo_kwh = (potencia * horas_dia * dias_mes * cantidad) / 1000
                
                payload = {
                    "id": aparato_existente['id'],
                    "nombre": aparato_existente['nombre'],
                    "cantidad": cantidad,
                    "potencia": potencia,
                    "eficiencia": eficiencia,
                    "horas_dia": horas_dia,
                    "dias_mes": dias_mes,
                    "consumo_kwh": round(consumo_activo_kwh, 2),
                    "total_kwh": round(consumo_activo_kwh, 2)
                }
                try:
                    respuesta = requests.put(f"{URL_API}/electrodomesticos/{estado.usuario_actual}/{aparato_existente['id']}", json=payload)
                    respuesta.raise_for_status()
                    st.success("Electrodoméstico actualizado exitosamente.")
                    st.cache_data.clear()
                    st.session_state.dialog_open = False
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"No se pudo actualizar el electrodoméstico: {e}")

@st.dialog("Registrar Factura")
def dialogo_registrar_factura():
    """Define la interfaz y lógica para el diálogo de registro de facturas."""
    with st.form(key="form_factura_manual"):
        st.subheader("Registrar Consumo Mensual")
        col1, col2 = st.columns(2)
        with col1:
            mes = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], key="dialog_mes")
            anio = st.selectbox("Año", list(range(datetime.now().year, 2019, -1)), key="dialog_anio")
        with col2:
            consumo_kwh = st.number_input("Consumo Total (kWh)", min_value=0.0, format="%.2f", key="dialog_kwh")
            costo = st.number_input("Costo Total (ARS $)", min_value=0.0, format="%.2f", key="dialog_costo")

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            enviado = st.form_submit_button("Guardar Factura", type="primary", use_container_width=True)
        with col_cancel:
            if st.form_submit_button("Cancelar", use_container_width=True):
                st.session_state.dialog_open = False
                st.rerun()

        if enviado:
            if consumo_kwh <= 0 or costo <= 0:
                st.warning("El consumo y el costo deben ser mayores a 0.")
            else:
                payload = {
                    "id": str(uuid.uuid4()),
                    "mes": mes,
                    "anio": int(anio),
                    "consumo_kwh": consumo_kwh,
                    "costo": costo
                }
                try:
                    respuesta = requests.post(f"{URL_API}/facturas/{estado.usuario_actual}", json=payload)
                    respuesta.raise_for_status()
                    st.success("Factura guardada exitosamente.")
                    st.cache_data.clear()
                    st.session_state.dialog_open = False
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"Error al guardar factura: {e}")

# ---------- FUNCIONES DE CARGA DE DATOS DEL BACKEND ----------

@st.cache_data(ttl=3600)
def cargar_datos_facturas():
    """Carga las facturas del usuario desde el backend."""
    try:
        respuesta = requests.get(f"{URL_API}/facturas/{estado.usuario_actual}")
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.exceptions.ConnectionError:
        st.error("Error de conexión con el servidor. Verifica que el backend esté activo.")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.error("Usuario no encontrado. Asegúrate de haber iniciado sesión correctamente.")
        else:
            st.error(f"Error al cargar facturas: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error inesperado al cargar facturas: {e}")
        return None

@st.cache_data(ttl=3600)
def cargar_datos_electrodomesticos():
    """Carga los electrodomésticos del usuario desde el backend."""
    try:
        respuesta = requests.get(f"{URL_API}/electrodomesticos/{estado.usuario_actual}")
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.exceptions.ConnectionError:
        st.error("Error de conexión con el servidor. Verifica que el backend esté activo.")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.error("Usuario no encontrado. Asegúrate de haber iniciado sesión correctamente.")
        else:
            st.error(f"Error al cargar electrodomésticos: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error inesperado al cargar electrodomésticos: {e}")
        return None

@st.cache_data(ttl=3600)
def cargar_catalogo_electrodomesticos():
    """Carga el catálogo general de electrodomésticos desde el backend y lo limita a 50 items."""
    try:
        respuesta = requests.get(f"{URL_API}/catalogo/electrodomesticos")
        respuesta.raise_for_status()
        full_catalog = respuesta.json()
        return full_catalog[:50]
    except requests.exceptions.ConnectionError:
        st.error("Error de conexión con el servidor. Verifica que el backend esté activo.")
        return []
    except requests.exceptions.HTTPError as e:
        st.error(f"Error al cargar el catálogo de electrodomésticos: {e}.")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error inesperado al cargar el catálogo de electrodomesticos: {e}.")
        return []

@st.cache_data(ttl=3600)
def cargar_metricas_resumen():
    """Carga las métricas de resumen para la página de inicio."""
    try:
        respuesta = requests.get(f"{URL_API}/metricas/resumen/{estado.usuario_actual_id}")
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.exceptions.ConnectionError:
        st.error("Error de conexión con el servidor. Verifica que el backend esté activo.")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.error("Usuario no encontrado. Asegúrate de haber iniciado sesión correctamente.")
        else:
            st.error(f"Error al cargar métricas de resumen: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error inesperado al cargar métricas de resumen: {e}")
        return None

@st.cache_data(ttl=3600)
def cargar_metricas_perfil():
    """Carga las métricas detalladas y el progreso para la página de perfil."""
    try:
        respuesta = requests.get(f"{URL_API}/metricas/perfil/{estado.usuario_actual_id}")
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.exceptions.ConnectionError:
        st.error("Error de conexión con el servidor. Verifica que el backend esté activo.")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.error("Usuario no encontrado. Asegúrate de haber iniciado sesión correctamente.")
        else:
            st.error(f"Error al cargar métricas del perfil: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error inesperado al cargar métricas del perfil: {e}")
        return None

@st.cache_data(ttl=3600)
def cargar_consejos():
    """Carga los consejos de sostenibilidad para el usuario."""
    try:
        respuesta = requests.get(f"{URL_API}/consejos/{estado.usuario_actual_id}")
        respuesta.raise_for_status()
        return respuesta.json().get("consejos", [])
    except requests.exceptions.ConnectionError:
        st.error("Error de conexión con el servidor. Verifica que el backend esté activo.")
        return []
    except requests.exceptions.HTTPError as e:
        st.error(f"Error al cargar consejos de sostenibilidad: {e}.")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error inesperado al cargar consejos de sostenibilidad: {e}.")
        return []

# ---------- VISTAS PRINCIPALES DE LA APLICACIÓN ----------

def mostrar_inicio_sesion():
    """Muestra la página de inicio de sesión y registro."""
    st.markdown("<h1 class='main-title'>GreenCalc ♻️</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Tu compañero para un consumo inteligente y sostenible.</p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, col_main, _ = st.columns([1, 1.5, 1])
    with col_main:
        with st.container(border=True):
            tab_login, tab_register = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
            
            with tab_login:
                st.subheader("Bienvenido de nuevo")
                with st.form(key="login_form"):
                    correo = st.text_input("Correo electrónico (usuario)", value="usuario1@example.com")
                    contrasena = st.text_input("Contraseña", type="password", value="password123")
                    if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                        try:
                            peticion = {"username": correo, "password": contrasena}
                            respuesta = requests.post(f"{URL_API}/login", json=peticion)
                            respuesta.raise_for_status()
                            datos_respuesta = respuesta.json()
                            
                            estado.sesion_iniciada = True
                            estado.usuario_actual = correo
                            estado.usuario_actual_id = datos_respuesta.get("usuario_id")
                            
                            try:
                                perfil_respuesta = requests.get(f"{URL_API}/usuarios/{estado.usuario_actual_id}")
                                perfil_respuesta.raise_for_status()
                                perfil_usuario = perfil_respuesta.json()
                                estado.usuario_actual_nombre = perfil_usuario.get("nombre", "Usuario")
                            except requests.exceptions.RequestException:
                                estado.usuario_actual_nombre = "Usuario"

                            estado.pagina_actual = "resumen_general"
                            st.rerun()
                        except requests.exceptions.ConnectionError:
                            st.error("Error de conexión con el servidor. Verifica que el backend esté activo.")
                        except requests.exceptions.HTTPError as e:
                            st.error(f"Error al iniciar sesión: {e}. Credenciales incorrectas o error de conexión.")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Error inesperado al iniciar sesión: {e}.")

            with tab_register:
                with st.form(key="register_form", clear_on_submit=True):
                    st.subheader("Crea tu cuenta")
                    nombre = st.text_input("Nombre Completo", key="reg_nombre")
                    correo_nuevo = st.text_input("Correo electrónico (será tu usuario)", key="reg_correo")
                    pass_nueva = st.text_input("Contraseña", type="password", key="reg_pass1")
                    pass_confirm = st.text_input("Confirmar Contraseña", type="password", key="reg_pass2")
                    ubicacion = st.selectbox("Ubicación", ["Resistencia, Chaco", "Corrientes", "Buenos Aires", "Córdoba", "Santa Fe", "Otra"], key="reg_ubicacion")
                    nivel_subsidio = st.selectbox("Nivel de Subsidio", ["alto", "medio", "bajo"], key="reg_subsidio")

                    if st.form_submit_button("Crear Cuenta", type="primary", use_container_width=True):
                        if pass_nueva != pass_confirm:
                            st.error("Las contraseñas no coinciden.")
                        elif not correo_nuevo or not nombre:
                            st.error("Por favor, completa todos los campos.")
                        else:
                            try:
                                peticion = {"username": correo_nuevo, "password": pass_nueva, "nombre": nombre, "ubicacion": ubicacion, "nivel_subsidio": nivel_subsidio}
                                respuesta = requests.post(f"{URL_API}/registro", json=peticion)
                                respuesta.raise_for_status()
                                st.success("¡Cuenta creada exitosamente! Por favor, inicia sesión.")
                            except requests.exceptions.ConnectionError:
                                st.error("Error de conexión con el servidor. Verifica que el backend esté activo.")
                            except requests.exceptions.HTTPError as e:
                                st.error(f"Error al registrar: {e}. El usuario ya podría existir o hubo un problema de conexión.")
                            except requests.exceptions.RequestException as e:
                                st.error(f"Error inesperado al registrar: {e}.")
    st.markdown("<br><br>", unsafe_allow_html=True)

def mostrar_resumen_general():
    """Página principal de la aplicación con un resumen del impacto del usuario."""
    st.title(f"¡Bienvenido a GreenCalc, {estado.usuario_actual_nombre}! 🌿")
    st.markdown("<p style='text-align: center;'>Aquí puedes ver un resumen de tu impacto energético y de sostenibilidad.</p>", unsafe_allow_html=True)

    st.subheader("Tu Resumen Energético")
    metricas = cargar_metricas_resumen()
    
    if metricas:
        facturas_data = cargar_datos_facturas()
        if facturas_data:
            df_facturas = pd.DataFrame(facturas_data)
            meses_orden = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            df_facturas['mes_num'] = df_facturas['mes'].apply(lambda m: meses_orden.index(m))
            df_facturas_sorted = df_facturas.sort_values(by=['anio', 'mes_num'], ascending=False)

            if len(df_facturas_sorted) >= 2:
                consumo_ultimo_mes = df_facturas_sorted.iloc[0]['consumo_kwh']
                consumo_mes_anterior = df_facturas_sorted.iloc[1]['consumo_kwh']

                if consumo_mes_anterior > 0:
                    cambio_porcentaje = ((consumo_ultimo_mes - consumo_mes_anterior) / consumo_mes_anterior) * 100
                    if cambio_porcentaje > 0:
                        st.warning(f"📉 Tu consumo subió {cambio_porcentaje:.2f}% vs el mes pasado ({df_facturas_sorted.iloc[1]['mes']} {df_facturas_sorted.iloc[1]['anio']}). ¡Revisa tus hábitos!")
                    elif cambio_porcentaje < 0:
                        st.success(f"📈 ¡Excelente! Tu consumo bajó {-cambio_porcentaje:.2f}% vs el mes pasado ({df_facturas_sorted.iloc[1]['mes']} {df_facturas_sorted.iloc[1]['anio']}). ¡Sigue así!")
                    else:
                        st.info("Tu consumo se mantuvo igual que el mes pasado.")
                else:
                    st.info("No hay consumo en el mes anterior para comparar.")
            elif len(df_facturas_sorted) == 1:
                st.info("Necesitas al menos dos meses de facturas para comparar el consumo.")

        col_consumo, col_costo, col_huella, col_puntos = st.columns(4)
        with col_consumo:
            st.metric(label="Consumo Total (kWh)", value=f"{metricas['consumo_total_kwh']:.2f} kWh")
        with col_costo:
            st.metric(label="Costo Total ($)", value=f"${metricas['costo_total']:.2f}")
        with col_huella:
            st.metric(label="Huella CO₂ (kg)", value=f"{metricas['huella_co2_total']:.2f} kg CO₂")
        with col_puntos:
            st.metric(label="Puntos de Sostenibilidad 🌱", value=metricas['puntos_sostenibilidad'])

        st.divider()
        
        st.subheader("Resumen de Actividad")
        resumen_actividad = metricas.get("resumen_actividad", {})
        if resumen_actividad:
            data = {
                "Métrica": ["Consumo (kWh)", "Costo (ARS)"],
                "Facturas (Real)": [resumen_actividad.get("facturas_consumo", 0), resumen_actividad.get("facturas_costo", 0)],
                "Electrodomésticos (Estimado)": [resumen_actividad.get("estimado_consumo", 0), resumen_actividad.get("estimado_costo", 0)]
            }
            df_resumen = pd.DataFrame(data)
            styled_df_resumen = df_resumen.style.format({
                "Facturas (Real)": "{:,.2f}",
                "Electrodomésticos (Estimado)": "{:,.2f}"
            }).background_gradient(
                cmap='Greens', subset=['Facturas (Real)', 'Electrodomésticos (Estimado)']
            )
            st.dataframe(styled_df_resumen, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos de resumen de actividad para mostrar. Registra facturas y electrodomésticos.")

        st.divider()

        st.subheader("Consejo Sostenible del Día")
        consejo = metricas.get('consejo_dinamico')
        if consejo:
            st.info(f"💡 **Consejo:** {consejo['texto']}{' ⚠️ (Urgente)' if consejo.get('urgente', False) else ''}")
        else:
            st.info("No hay consejos disponibles en este momento.")
        
        st.divider()

        st.subheader("Desglose de Consumo por Electrodoméstico")
        df_desglose = pd.DataFrame(metricas.get('desglose_electrodomesticos', []))
        if not df_desglose.empty and df_desglose["total_kwh"].sum() > 0:
            fig_height = 400
            fig = px.pie(df_desglose, names="nombre", values="total_kwh", hole=0.4,
                        title="Consumo por tipo de electrodoméstico", height=fig_height)
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay consumo estimado de electrodomésticos para mostrar un gráfico. ¡Añade algunos en la sección 'Electrodomésticos'!")
    else:
        st.warning("No se pudieron cargar las métricas de resumen. Por favor, asegúrate de que el backend esté funcionando y que hayas iniciado sesión correctamente.")
    st.divider()


def mostrar_perfil():
    """Página de perfil del usuario con configuración y métricas de impacto."""
    st.title("Información Personal 👤")

    datos_perfil = cargar_metricas_perfil()

    if datos_perfil:
        col_name, col_email = st.columns(2)
        with col_name:
            st.markdown(f"""
            <div class="profile-info-card">
                <span class="profile-info-card-icon">🧑</span>
                <div class="profile-info-card-content">
                    <strong>Nombre</strong>
                    <span>{estado.usuario_actual_nombre}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_email:
            st.markdown(f"""
            <div class="profile-info-card">
                <span class="profile-info-card-icon">📧</span>
                <div class="profile-info-card-content">
                    <strong>Correo electrónico (Usuario)</strong>
                    <span>{estado.usuario_actual}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        col_location, col_subsidio = st.columns(2)
        with col_location:
            st.markdown(f"""
            <div class="profile-info-card">
                <span class="profile-info-card-icon">📍</span>
                <div class="profile-info-card-content">
                    <strong>Ubicación</strong>
                    <span>{datos_perfil.get('ubicacion', 'N/A')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_subsidio:
            nivel_subsidio_display = {
                "alto": "N1",
                "medio": "N3",
                "bajo": "N2"
            }.get(datos_perfil.get('nivel_subsidio', 'N/A'), 'N/A')
            st.markdown(f"""
            <div class="profile-info-card">
                <span class="profile-info-card-icon">💰</span>
                <div class="profile-info-card-content">
                    <strong>Nivel de Subsidio</strong>
                    <span>{nivel_subsidio_display}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        st.subheader("Tu Impacto Sostenible")
        col_puntos, col_emisiones = st.columns(2)
        with col_puntos:
            st.markdown(
                f"""
                <div class="stMetric">
                    <label class="stMetricLabel">Puntos de Sostenibilidad</label><br>
                    <div class="stMetricValue">{datos_perfil.get("puntos_sostenibilidad", 0)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_emisiones:
            st.markdown(
                f"""
                <div class="stMetric">
                    <label class="stMetricLabel">Emisiones de la Sesión (kg CO₂)</label><br>
                    <div class="stMetricValue">{datos_perfil.get('emisiones_sesion_kg_co2', 0):.2f}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.divider()

        with st.expander("⚙️ Configuración de Perfil", expanded=True):
            with st.form("form_config_perfil"):
                nuevo_nombre = st.text_input("Nombre", value=estado.usuario_actual_nombre, key="perfil_nombre")
                nueva_ubicacion_opciones = ["Resistencia, Chaco", "15000"]
                current_ubicacion_index = nueva_ubicacion_opciones.index(datos_perfil.get('ubicacion', 'Resistencia, Chaco')) if datos_perfil.get('ubicacion') in nueva_ubicacion_opciones else 0
                nueva_ubicacion = st.selectbox("Ubicación", nueva_ubicacion_opciones, index=current_ubicacion_index, key="perfil_ubicacion")
                
                nivel_subsidio_opciones_form = ["N1", "N2", "N3"]
                nivel_subsidio_backend_map = {
                    "N1": "alto",
                    "N2": "bajo",
                    "N3": "medio"
                }
                current_subsidio_value_from_backend = datos_perfil.get('nivel_subsidio', 'medio')
                current_subsidio_display_value = {v: k for k, v in nivel_subsidio_backend_map.items()}.get(current_subsidio_value_from_backend, "N3")
                current_subsidio_index = nivel_subsidio_opciones_form.index(current_subsidio_display_value) if current_subsidio_display_value in nivel_subsidio_opciones_form else 2

                nuevo_nivel_subsidio_display = st.selectbox("Nivel de Subsidio", nivel_subsidio_opciones_form, index=current_subsidio_index, key="perfil_subsidio")
                nuevo_nivel_subsidio_backend = nivel_subsidio_backend_map.get(nuevo_nivel_subsidio_display, "medio")
                
                nueva_contrasena = st.text_input("Nueva Contraseña (dejar vacío para no cambiar)", type="password", key="perfil_pass1")
                confirmar_contrasena = st.text_input("Confirmar Nueva Contraseña", type="password", key="perfil_pass2")

                col_guardar = st.columns(1)[0]
                with col_guardar:
                    if st.form_submit_button("Guardar Cambios", type="primary", use_container_width=True):
                        if nueva_contrasena and nueva_contrasena != confirmar_contrasena:
                            st.error("Las nuevas contraseñas no coinciden.")
                        else:
                            try:
                                payload = {
                                    "nombre": nuevo_nombre,
                                    "ubicacion": nueva_ubicacion,
                                    "nivel_subsidio": nuevo_nivel_subsidio_backend
                                }
                                if nueva_contrasena:
                                    payload["password"] = nueva_contrasena
                                
                                respuesta = requests.put(f"{URL_API}/usuarios/{estado.usuario_actual_id}", json=payload)
                                respuesta.raise_for_status()
                                st.success("Perfil actualizado exitosamente.")
                                estado.usuario_actual_nombre = nuevo_nombre
                                st.cache_data.clear()
                                st.rerun()
                            except requests.exceptions.ConnectionError:
                                st.error("Error de conexión con el servidor. Verifica que el backend esté activo.")
                            except requests.exceptions.HTTPError as e:
                                st.error(f"Error al actualizar perfil: {e}")
                            except requests.exceptions.RequestException as e:
                                st.error(f"Error inesperado al actualizar perfil: {e}.")
        
        st.divider()

        if st.button("Cerrar Sesión", use_container_width=True, key="cerrar_sesion_btn_perfil"):
            estado.sesion_iniciada = False
            estado.usuario_actual = ""
            estado.usuario_actual_id = None
            estado.usuario_actual_nombre = ""
            estado.pagina_actual = "inicio_sesion"
            st.rerun()

    else:
        st.warning("No se pudo cargar la información del perfil.")
    
    st.divider()
    if estado.usuario_actual == "admin@example.com":
        estado.modo_administrador = st.checkbox("Activar Modo Administrador", value=estado.modo_administrador)
        if estado.modo_administrador:
            st.subheader("Panel de Administrador")
            st.info("Funcionalidades de administrador en desarrollo para el mock.")
            if st.button("Generar Datos de Prueba", key="admin_generar_datos_btn"):
                try:
                    requests.post(f"{URL_API}/generar_datos_prueba/{estado.usuario_actual}").raise_for_status()
                    st.success("Datos de prueba generados.")
                    st.cache_data.clear()
                    st.rerun()
                except requests.exceptions.ConnectionError:
                    st.error("Error de conexión con el servidor. Verifica que el backend esté activo.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error al generar datos: {e}")
            if st.button("Restablecer Puntos de Sostenibilidad (Solo Local)", key="admin_reset_puntos"):
                estado.puntos_sostenibilidad = 0
                estado.consejos_cumplidos = []
                st.success("Puntos y consejos restablecidos localmente.")
                st.cache_data.clear()
                st.rerun()
            if st.button("Desactivar Modo Administrador", key="admin_desactivar"):
                estado.modo_administrador = False
                st.rerun()
    st.divider()


def mostrar_facturas():
    """Página de gestión de facturas de energía."""
    st.title("Análisis de Facturas 📄")

    with st.container(border=True):
        st.subheader("Acciones de Facturación")
        col_add_manual, col_upload_ocr = st.columns(2)

        with col_add_manual:
            if st.button("➕ Añadir Nueva Factura", use_container_width=True, key="add_factura_btn"):
                dialogo_registrar_factura()

        with col_upload_ocr:
            if st.button("⬆️ Subir Factura (OCR)", use_container_width=True, key="upload_ocr_btn"):
                dialogo_subir_ocr()

    st.divider()

    lista_facturas = cargar_datos_facturas()

    if lista_facturas is None:
        return

    if not lista_facturas:
        st.info("Aún no has registrado facturas.")
        return

    st.header("Panel de Análisis de Consumo")
    df_facturas = pd.DataFrame(lista_facturas)

    lista_anios = sorted(df_facturas["anio"].unique(), reverse=True)
    anio_seleccionado = st.selectbox("Selecciona un año para analizar:", lista_anios, key="fact_anio_sel")

    df_seleccionado = df_facturas[df_facturas["anio"] == anio_seleccionado].copy()

    total_kwh_anual = df_seleccionado["consumo_kwh"].sum()
    total_costo_anual = df_seleccionado["costo"].sum()
    
    costo_estimado = 0
    huella_kg = 0
    
    if total_kwh_anual > 0:
        try:
            perfil_data = requests.get(f"{URL_API}/usuarios/{estado.usuario_actual_id}").json()
            nivel_subsidio_usuario = perfil_data.get("nivel_subsidio", "medio")
            
            payload_calc = {"kwh": total_kwh_anual, "nivel_subsidio": nivel_subsidio_usuario}
            costo_res = requests.post(f"{URL_API}/calcular/costo", json=payload_calc)
            costo_res.raise_for_status()
            costo_estimado = costo_res.json()["costo_estimado"]
            
            huella_res = requests.post(f"{URL_API}/calcular/huella_carbono", json=payload_calc)
            huella_res.raise_for_status()
            huella_kg = huella_res.json()["huella_carbono_kg_co2"]
        except requests.exceptions.ConnectionError:
            st.warning("No se pudo conectar con el servidor para calcular métricas estimadas.")
        except requests.exceptions.RequestException as e:
            st.warning(f"No se pudieron calcular las métricas estimadas: {e}.")

    st.subheader(f"Resumen del Año {anio_seleccionado}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Consumo Anual Total", f"{total_kwh_anual:.2f} kWh")
    col2.metric("Costo Anual Real", f"${total_costo_anual:,.2f}")
    col3.metric("Costo Anual Estimado", f"${costo_estimado:,.2f}")
    col4.metric("Huella de Carbono", f"{huella_kg:.2f} kg CO₂")
    
    if total_costo_anual > costo_estimado * 1.2 and costo_estimado > 0:
        st.warning(f"¡Atención! Tu costo real (${total_costo_anual:,.2f}) es más de un 20% superior al costo estimado (${costo_estimado:,.2f}) para tu consumo.")

    st.divider()

    st.subheader("Análisis Mensual")
    meses_ordenados = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    df_seleccionado['mes'] = pd.Categorical(df_seleccionado['mes'], categories=meses_ordenados, ordered=True)
    df_grafico = df_seleccionado.sort_values('mes')

    tipo_grafico = st.selectbox("Tipo de gráfico", ["Barras", "Línea", "Área"], key="fact_tipo_graf")
    
    fig_height = 400
    col_graf_1, col_graf_2 = st.columns(2)
    with col_graf_1:
        if tipo_grafico == "Barras":
            fig = px.bar(df_grafico, x="mes", y="consumo_kwh", height=fig_height)
        elif tipo_grafico == "Línea":
            fig = px.line(df_grafico, x="mes", y="consumo_kwh", markers=True, height=fig_height)
        else:
            fig = px.area(df_grafico, x="mes", y="consumo_kwh", height=fig_height)
        fig.update_layout(title_text='Consumo Mensual (kWh)', xaxis_title='Mes', yaxis_title='Consumo (kWh)')
        st.plotly_chart(fig, use_container_width=True)

    with col_graf_2:
        if tipo_grafico == "Barras":
            fig2 = px.bar(df_grafico, x="mes", y="costo", color_discrete_sequence=['#FFB74D'], height=fig_height)
        elif tipo_grafico == "Línea":
            fig2 = px.line(df_grafico, x="mes", y="costo", markers=True, color_discrete_sequence=['#FFB74D'], height=fig_height)
        else:
            fig2 = px.area(df_grafico, x="mes", y="costo", color_discrete_sequence=['#FFB74D'], height=fig_height)
        fig2.update_layout(title_text='Costo Mensual (ARS)', xaxis_title='Mes', yaxis_title='Costo (ARS)')
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Ver detalle de facturas en tabla"):
        df_display = df_seleccionado[["mes", "anio", "consumo_kwh", "costo"]].copy()
        df_display.rename(columns={"consumo_kwh": "Consumo (kWh)", "costo": "Costo (ARS)"}, inplace=True)
        
        styled_df = df_display.style.format({
            "Consumo (kWh)": "{:.2f}",
            "Costo (ARS)": "${:,.2f}"
        }).background_gradient(
            cmap='Greens', subset=['Consumo (kWh)']
        ).background_gradient(
            cmap='YlOrRd', subset=['Costo (ARS)']
        )
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    st.divider()


def mostrar_electrodomesticos():
    """Página para gestionar el inventario de electrodomésticos del usuario."""
    st.title("Gestión de Electrodomésticos 🔌")

    iconos_electrodomesticos = {
        "Heladera c/freezer (moderno)": "🧊", "Freezer independiente": "❄️",
        "TV LED 40\"": "📺", "TV LED 19\"": "📺", "Laptop/Notebook": "💻",
        "Pava eléctrica": "☕", "Plancha": "👕", "Secarropas térmico": "💨",
        "Secarropas centrífugo": "🌀", "Lavavajillas 12 cubiertos": "🍽️",
        "Bomba de agua 1/2 HP": "💧", "Bomba de agua 3/4 HP": "💧",
        "Anafe vitrocerámico": "🔥", "Aspiradora": "🧹", "Computadora": "🖥️",
        "Monitor LED 19\"": "🖥️", "Cargador de Celular": "📱", "Aire Acondicionado": "🌬️",
        "Lavarropas": "🧺", "Microondas": "♨️", "Horno Eléctrico": "🍞",
        "Calefactor Eléctrico": "♨️", "Ventilador de techo": "🌬️", "Ventilador de pie": "🌬️",
        "Estufa eléctrica": "🔥", "Cafetera": "☕", "Tostadora": "🍞",
        "Licuadora": "🥤", "Batidora": "🥣", "Equipo de sonido": "🔊",
        "Cámara de seguridad": "📹", "Reproductor de DVD/Blu-ray": "📀",
        "Consola de videojuegos": "🎮", "Impresora": "🖨️", "Router Wi-Fi": "📶",
        "Decodificador TV Cable/Satélite": "📡", "Termotanque eléctrico (80L)": "💧",
        "Caloventor": "🔥", "Máquina de coser": "🧵", "Home Theater": "🎬",
        "Cava de vinos": "🍷", "Bicicleta fija/Cinta de correr": "🚴",
        "Horno a gas": "🔥", "Calefón a gas c/piloto (genérico)": "🔥",
        "Termotanque a gas (genérico)": "🔥", "Cocina a gas": "🍳",
        "Estufa a gas": "🔥", "Secarropas a gas": "💨", "Parrilla a gas": "🔥",
        "Triturador de basura": "🗑️", "Deshumidificador": "💧", "Purificador de aire": "🍃",
        "Corta césped eléctrica": "🌱", "Bomba de pileta": "🏊", "Secador de pelo": "💇‍♀️",
        "Bomba presurizadora": "ポンプ", "Herramientas eléctricas (taladro, sierra)": "🛠️",
    }


    st.subheader("Catálogo Rápido")
    if "catalogo_electrodomesticos" not in st.session_state or not st.session_state.catalogo_electrodomesticos:
        st.session_state.catalogo_electrodomesticos = cargar_catalogo_electrodomesticos()
    
    inventario = cargar_datos_electrodomesticos()
    nombres_en_inventario = {aparato['nombre'] for aparato in (inventario if inventario is not None else [])}

    if st.session_state.catalogo_electrodomesticos:
        st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
        cols = st.columns(5)
        for i, datos_aparato_catalogo in enumerate(st.session_state.catalogo_electrodomesticos):
            nombre_aparato = datos_aparato_catalogo.get('nombre', 'Desconocido')
            ya_existe = nombre_aparato in nombres_en_inventario
            
            with cols[i % 5]:
                icono = iconos_electrodomesticos.get(nombre_aparato, "⚡")
                if st.button(
                    f"{icono} {nombre_aparato}",
                    key=f"cat_{nombre_aparato}", 
                    use_container_width=True,
                    disabled=ya_existe
                ):
                    dialogo_configurar_electrodomestico(nombre_aparato, datos_aparato_catalogo)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No se pudo cargar el catálogo de electrodomésticos. No puedes añadir nuevos.")

    st.divider()

    st.subheader("Mi Inventario")

    if inventario is None:
        return

    if not inventario:
        st.info("Aún no has añadido electrodomésticos.")
        return
        
    else:
        df_inventario = pd.DataFrame(inventario)
        df_inventario["total_kwh"] = (df_inventario["potencia"] * df_inventario["horas_dia"] * df_inventario["dias_mes"] * df_inventario["cantidad"]) / 1000

        total_kwh_inventario = df_inventario["total_kwh"].sum()
        costo_estimado_inventario = 0.0
        carbono_inventario = 0.0
        
        try:
            perfil_data = requests.get(f"{URL_API}/usuarios/{estado.usuario_actual_id}").json()
            nivel_subsidio_usuario = perfil_data.get("nivel_subsidio", "medio")

            payload_calc = {"kwh": total_kwh_inventario, "nivel_subsidio": nivel_subsidio_usuario}
            costo_res = requests.post(f"{URL_API}/calcular/costo", json=payload_calc)
            costo_res.raise_for_status()
            costo_estimado_inventario = costo_res.json()["costo_estimado"]
            
            huella_res = requests.post(f"{URL_API}/calcular/huella_carbono", json=payload_calc)
            huella_res.raise_for_status()
            carbono_inventario = huella_res.json()["huella_carbono_kg_co2"]
            arboles_eq = carbono_inventario / 21

        except requests.exceptions.ConnectionError:
            st.warning("No se pudo conectar con el servidor para calcular métricas estimadas del inventario.")
        except requests.exceptions.RequestException as e:
            st.warning(f"No se pudieron calcular las métricas estimadas del inventario: {e}.")
            
        col1, col2, col3 = st.columns(3)
        col1.metric("Consumo Estimado", f"{total_kwh_inventario:.2f} kWh/mes")
        col2.metric("Costo Estimado", f"${costo_estimado_inventario:,.2f} ARS/mes")
        col3.metric("Huella CO₂", f"{carbono_inventario:.2f} kg CO₂", f"~{arboles_eq:.2f} árboles/año")

        st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
        for i, aparato in df_inventario.iterrows():
            icono = iconos_electrodomesticos.get(aparato['nombre'], "⚡")
            
            col_item_icon, col_item_details, col_item_actions = st.columns([0.1, 0.7, 0.2])
            
            with col_item_icon:
                st.markdown(f'<span class="appliance-item-icon">{icono}</span>', unsafe_allow_html=True)
            
            with col_item_details:
                st.markdown(f"""
                    <div class="appliance-item-details">
                        <strong>{aparato['cantidad']}x {aparato['nombre']}</strong><br>
                        Consumo: {aparato['total_kwh']:.2f} kWh/mes
                    </div>
                """, unsafe_allow_html=True)
            
            with col_item_actions:
                st.button("✏️", key=f"editar_{aparato['id']}", help="Editar electrodoméstico", on_click=lambda ap=aparato.to_dict(): dialogo_editar_electrodomestico(ap), args=None, use_container_width=True)
                st.button("🗑️", key=f"eliminar_{aparato['id']}", help="Eliminar del inventario", on_click=lambda ap_id=aparato['id']: requests.delete(f"{URL_API}/electrodomesticos/{estado.usuario_actual}/{ap_id}") and st.success("Electrodoméstico eliminado.") and st.cache_data.clear() and st.rerun(), args=None, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        
        st.subheader("Distribución del Consumo Estimado")
        if not df_inventario.empty and df_inventario["total_kwh"].sum() > 0:
            fig_height = 400
            fig = px.pie(df_inventario, names="nombre", values="total_kwh", hole=0.4,
                        title="Consumo por tipo de electrodoméstico", height=fig_height)
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay consumo registrado para mostrar un gráfico. Asegúrate de que tus aparatos tengan potencia y horas de uso configuradas.")  
    st.divider()


def mostrar_consejos():
    """Página con consejos de sostenibilidad personalizados."""
    st.title("Consejos de Sostenibilidad 💡")
    
    st.subheader("Tu Impacto Energético Promedio")
    metricas_perfil = cargar_metricas_perfil()
    if metricas_perfil:
        consumo_promedio = metricas_perfil.get("resumen_actividad", {}).get("facturas_consumo", 0) / 12
        costo_promedio = metricas_perfil.get("resumen_actividad", {}).get("facturas_costo", 0) / 12
        huella_promedio = (requests.post(f"{URL_API}/calcular/huella_carbono", json={"kwh": consumo_promedio, "nivel_subsidio": "medio"}).json().get("huella_carbono_kg_co2", 0)) if consumo_promedio > 0 else 0

        fig_gauge_height = 300 

        col_consumo_m, col_costo_m, col_huella_m = st.columns(3)
        with col_consumo_m:
            fig_consumo = go.Figure(go.Indicator(
                mode="gauge+number",
                value=consumo_promedio,
                title={'text': "Consumo Mensual Promedio (kWh)"},
                gauge={'axis': {'range': [0, 500], 'tickvals': [0, 100, 200, 300, 400, 500]}, # Set max value and tick values
                       'bar': {'color': "#81C784"},
                       'steps': [
                           {'range': [0, 150], 'color': "#E8F5E9"},
                           {'range': [150, 300], 'color': "#A5D6A7"},
                           {'range': [300, 500], 'color': "#FF8A65"}],
                       'threshold': {'line': {'color': "#EF5350", 'width': 4}, 'thickness': 0.75, 'value': 250}}))
            fig_consumo.update_layout(height=fig_gauge_height)
            st.plotly_chart(fig_consumo, use_container_width=True)
        with col_costo_m:
            fig_costo = go.Figure(go.Indicator(
                mode="gauge+number",
                value=costo_promedio,
                title={'text': "Costo Mensual Promedio (ARS)"},
                gauge={'axis': {'range': [0, 50000], 'tickvals': [0, 10000, 20000, 30000, 40000, 50000]}, # Set max value and tick values
                       'bar': {'color': "#FFB74D"},
                       'steps': [
                           {'range': [0, 15000], 'color': "#FFF3E0"},
                           {'range': [15000, 30000], 'color': "#FFCC80"},
                           {'range': [30000, 50000], 'color': "#FF8A65"}],
                       'threshold': {'line': {'color': "#EF5350", 'width': 4}, 'thickness': 0.75, 'value': 25000}}))
            fig_costo.update_layout(height=fig_gauge_height)
            st.plotly_chart(fig_costo, use_container_width=True)
        with col_huella_m:
            fig_huella = go.Figure(go.Indicator(
                mode="gauge+number",
                value=huella_promedio,
                title={'text': "Huella CO₂ Mensual Promedio (kg)"},
                gauge={'axis': {'range': [0, 150], 'tickvals': [0, 30, 60, 90, 120, 150]}, # Set max value and tick values
                       'bar': {'color': "#64B5F6"},
                       'steps': [
                           {'range': [0, 45], 'color': "#E3F2FD"},
                           {'range': [45, 90], 'color': "#BBDEFB"},
                           {'range': [90, 150], 'color': "#FF8A65"}],
                       'threshold': {'line': {'color': "#EF5350", 'width': 4}, 'thickness': 0.75, 'value': 75}}))
            fig_huella.update_layout(height=fig_gauge_height)
            st.plotly_chart(fig_huella, use_container_width=True)
    else:
        st.info("No hay datos suficientes para mostrar el panel de impacto energético. Registra más facturas.")

    st.divider()

    st.subheader("Consejos Personalizados para ti")
    consejos_activos = cargar_consejos()

    if consejos_activos is None:
        return

    if consejos_activos:
        consejos_urgentes = [c for c in consejos_activos if c.get("urgente") and not c.get("cumplido")]
        consejos_normales = [c for c in consejos_activos if not c.get("urgente") and not c.get("cumplido")]
        consejos_cumplidos = [c for c in consejos_activos if c.get("cumplido")]

        if consejos_urgentes:
            st.markdown("<h3><span class='consejo-card-icon'>⚠️</span> Consejos Urgentes</h3>", unsafe_allow_html=True)
            for i in range(0, len(consejos_urgentes), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(consejos_urgentes):
                        consejo = consejos_urgentes[i+j]
                        with cols[j]:
                            checked = consejo.get("cumplido", False)
                            st.markdown(f"""
                            <div class="consejo-card urgente">
                                <div class="consejo-card-inner-content">
                                    <span class="consejo-card-icon">⚠️</span>
                                    <div class="consejo-card-text">
                                        <strong>{consejo['texto']}</strong>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            with st.container():
                                st.markdown('<div class="consejo-card-checkbox-wrapper">', unsafe_allow_html=True)
                                st.checkbox("Marcar como cumplido", value=checked, key=f"cb_urg_{consejo['id']}", 
                                            on_change=lambda c_id=consejo['id']: requests.post(f"{URL_API}/consejos/{estado.usuario_actual_id}/marcar_cumplido", json={"consejo_id": c_id}) and st.success("¡Consejo urgente cumplido! Has ganado puntos de sostenibilidad.") and st.cache_data.clear() and st.rerun(), 
                                            args=None, label_visibility="hidden")
                                st.markdown('</div>', unsafe_allow_html=True)

            st.divider()

        if consejos_normales:
            st.markdown("<h3><span class='consejo-card-icon'>💡</span> Otros Consejos</h3>", unsafe_allow_html=True)
            for i in range(0, len(consejos_normales), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(consejos_normales):
                        consejo = consejos_normales[i+j]
                        with cols[j]:
                            checked = consejo.get("cumplido", False)
                            st.markdown(f"""
                            <div class="consejo-card">
                                <div class="consejo-card-inner-content">
                                    <span class="consejo-card-icon">💡</span>
                                    <div class="consejo-card-text">
                                        {consejo['texto']}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            with st.container():
                                st.markdown('<div class="consejo-card-checkbox-wrapper">', unsafe_allow_html=True)
                                st.checkbox("Marcar como cumplido", value=checked, key=f"cb_norm_{consejo['id']}", 
                                            on_change=lambda c_id=consejo['id']: requests.post(f"{URL_API}/consejos/{estado.usuario_actual_id}/marcar_cumplido", json={"consejo_id": c_id}) and st.success("¡Consejo cumplido! Has ganado puntos de sostenibilidad.") and st.cache_data.clear() and st.rerun(), 
                                            args=None, label_visibility="hidden")
                                st.markdown('</div>', unsafe_allow_html=True)
            st.divider()
        
        if consejos_cumplidos:
            with st.expander("✅ Consejos ya cumplidos"):
                for i in range(0, len(consejos_cumplidos), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(consejos_cumplidos):
                            consejo = consejos_cumplidos[i+j]
                            with cols[j]:
                                st.markdown(f"""
                                <div class="consejo-card" style="opacity: 0.7; background-color: {st.get_option('theme.secondaryBackgroundColor')};">
                                    <div class="consejo-card-inner-content">
                                        <span class="consejo-card-icon">✅</span>
                                        <div class="consejo-card-text">
                                            <del>{consejo['texto']}</del>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
    else:
        st.info("No hay consejos de sostenibilidad disponibles en este momento. ¡Sigue registrando tus datos para recibir recomendaciones personalizadas!")
    st.divider()


# ---------- LÓGICA PRINCIPAL DE NAVEGACIÓN ----------
def mostrar_barra_navegacion():
    """
    Barra de navegación en formato «pastillas» minimalista usando botones de Streamlit.
    """
    tabs = {
        "resumen_general": "🏠 Inicio",
        "perfil": "👤 Perfil",
        "facturas": "📄 Facturas",
        "electrodomesticos": "🔌 Electrodomésticos",
        "consejos": "💡 Consejos"
    }

    st.markdown('<div class="nav-wrapper">', unsafe_allow_html=True)
    cols = st.columns(len(tabs))
    for idx, (key, label) in enumerate(tabs.items()):
        with cols[idx]:
            if st.button(label, key=f"nav_{key}", on_click=cambiar_pagina, args=(key,), use_container_width=True):
                pass
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Función principal que controla la navegación de la aplicación."""
    if not estado.sesion_iniciada:
        mostrar_inicio_sesion()
    else:
        mostrar_barra_navegacion()
        paginas = {
            "resumen_general": mostrar_resumen_general,
            "perfil": mostrar_perfil,
            "facturas": mostrar_facturas,
            "electrodomesticos": mostrar_electrodomesticos,
            "consejos": mostrar_consejos
        }
        funcion_pagina = paginas.get(estado.pagina_actual, mostrar_resumen_general)
        funcion_pagina()

if __name__ == "__main__":
    main()