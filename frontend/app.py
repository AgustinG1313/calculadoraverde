"""
Archivo principal de la aplicación Streamlit (Frontend).
Controla el estado de la sesión, la carga de CSS y la navegación entre páginas.
"""
import os
import streamlit as st
from components.navigation import mostrar_barra_navegacion
from auth import mostrar_inicio_sesion
from pages import summary, profile, invoices, appliances, advice

st.set_page_config(page_title="BioTrack", page_icon="🌱", layout="wide")

# --- Carga de CSS ---
def cargar_css(ruta_archivo):
    try:
        with open(ruta_archivo, encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"No se encontró el archivo CSS en: {ruta_archivo}")

ruta_css = os.path.join("frontend", "assets", "style.css")
cargar_css(ruta_css)

# --- Gestión del Estado de la Aplicación ---
class EstadoApp:
    def __init__(self):
        self.sesion_iniciada = False
        self.usuario_actual = ""
        self.usuario_actual_id = None
        self.pagina_actual = "resumen_general"

if "estado" not in st.session_state:
    st.session_state.estado = EstadoApp()
estado = st.session_state.estado

# --- Router Principal de la Aplicación ---
def main():
    if not estado.sesion_iniciada:
        mostrar_inicio_sesion(estado)
    else:
        mostrar_barra_navegacion()
        
        paginas = {
            "resumen_general": summary.mostrar_resumen_general,
            "perfil": profile.mostrar_perfil,
            "facturas": invoices.mostrar_facturas,
            "electrodomesticos": appliances.mostrar_electrodomesticos,
            "consejos": advice.mostrar_consejos,
        }
        
        # Obtiene la función de la página actual y la ejecuta
        pagina_a_mostrar = paginas.get(estado.pagina_actual, summary.mostrar_resumen_general)
        pagina_a_mostrar(estado)

if __name__ == "__main__":
    main()