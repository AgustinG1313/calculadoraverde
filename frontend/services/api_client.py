"""
Módulo para centralizar la comunicación con la API del backend.
Todas las funciones que realizan peticiones HTTP se encuentran aquí.
"""
import streamlit as st
import requests

URL_API = "http://127.0.0.1:8000"

def _handle_request(method, url, **kwargs):
    """Función de ayuda para manejar peticiones y errores comunes."""
    try:
        respuesta = requests.request(method, url, **kwargs)
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.exceptions.ConnectionError:
        st.error("Error de conexión: No se pudo conectar al servidor. Asegúrate de que el backend esté activo.")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.warning("Recurso no encontrado. Puede que el usuario o el dato no existan.")
        else:
            st.error(f"Error HTTP: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error inesperado en la petición: {e}")
        return None

@st.cache_data(ttl=60)
def cargar_datos_facturas(username):
    return _handle_request("get", f"{URL_API}/facturas/{username}")

@st.cache_data(ttl=60)
def cargar_datos_electrodomesticos(username):
    return _handle_request("get", f"{URL_API}/electrodomesticos/{username}")

@st.cache_data(ttl=3600)
def cargar_catalogo_electrodomesticos():
    catalogo = _handle_request("get", f"{URL_API}/catalogo/electrodomesticos")
    return catalogo[:50] if catalogo else []

@st.cache_data(ttl=60)
def cargar_metricas_resumen(user_id):
    return _handle_request("get", f"{URL_API}/metricas/resumen/{user_id}")

@st.cache_data(ttl=60)
def cargar_metricas_perfil(user_id):
    return _handle_request("get", f"{URL_API}/metricas/perfil/{user_id}")

@st.cache_data(ttl=60)
def cargar_consejos(user_id):
    data = _handle_request("get", f"{URL_API}/consejos/{user_id}")
    return data.get("consejos", []) if data else []

def marcar_consejo_cumplido(user_id, consejo_id):
    url = f"{URL_API}/consejos/{user_id}/marcar_cumplido"
    return _handle_request("post", url, json={"consejo_id": consejo_id})