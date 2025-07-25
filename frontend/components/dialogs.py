"""
Componentes de UI para todos los diálogos modales de la aplicación.
"""
import streamlit as st
import requests
import uuid
from datetime import datetime
from services.api_client import URL_API

@st.dialog("Subir Factura (OCR)")
def dialogo_subir_ocr():
    st.file_uploader("Arrastra tu archivo o haz clic para buscar", type=["pdf", "png", "jpg"], key="ocr_uploader")
    st.info("Funcionalidad de procesamiento OCR en desarrollo.")

@st.dialog("Configurar Electrodoméstico")
def dialogo_configurar_electrodomestico(nombre_aparato, datos_catalogo, estado_app):
    st.markdown(f"<p class='dialog-title'>Añadir {nombre_aparato}</p>", unsafe_allow_html=True)
    with st.form(key=f"form_add_{nombre_aparato}"):
        cantidad = st.number_input("Cantidad", min_value=1, value=1)
        potencia = st.number_input("Potencia (W)", min_value=0.0, value=float(datos_catalogo.get("potencia_base", 0)))
        horas_dia = st.number_input("Horas de uso/día", min_value=0.0, max_value=24.0, value=float(datos_catalogo.get("horas_dia_estandar", 1.0)), step=0.5)
        dias_mes = st.number_input("Días de uso/mes", min_value=1, max_value=31, value=int(datos_catalogo.get("dias_mes_estandar", 30)))
        
        if st.form_submit_button("Añadir al Inventario", type="primary", use_container_width=True):
            payload = {
                "id": str(uuid.uuid4()), "nombre": nombre_aparato, "cantidad": cantidad,
                "potencia": potencia, "eficiencia": "A", "horas_dia": horas_dia, "dias_mes": dias_mes
            }
            try:
                res = requests.post(f"{URL_API}/electrodomesticos/{estado_app.usuario_actual}", json=payload)
                res.raise_for_status()
                st.success("Electrodoméstico añadido.")
                st.cache_data.clear()
                st.rerun()
            except requests.RequestException as e:
                st.error(f"Error al añadir: {e}")

@st.dialog("Editar Electrodoméstico")
def dialogo_editar_electrodomestico(aparato, estado_app):
    st.markdown(f"<p class='dialog-title'>Editando ✏️ {aparato['nombre']}</p>", unsafe_allow_html=True)
    with st.form(key=f"form_edit_{aparato['id']}"):
        cantidad = st.number_input("Cantidad", min_value=1, value=aparato['cantidad'])
        potencia = st.number_input("Potencia (W)", min_value=0.0, value=float(aparato['potencia']))
        horas_dia = st.number_input("Horas de uso/día", min_value=0.0, max_value=24.0, value=float(aparato['horas_dia']), step=0.5)
        dias_mes = st.number_input("Días de uso/mes", min_value=1, max_value=31, value=int(aparato['dias_mes']))
        
        if st.form_submit_button("Guardar Cambios", type="primary", use_container_width=True):
            payload = {
                "cantidad": cantidad, "potencia": potencia,
                "horas_dia": horas_dia, "dias_mes": dias_mes
            }
            try:
                res = requests.put(f"{URL_API}/electrodomesticos/{estado_app.usuario_actual}/{aparato['id']}", json=payload)
                res.raise_for_status()
                st.success("Electrodoméstico actualizado.")
                st.cache_data.clear()
                st.rerun()
            except requests.RequestException as e:
                st.error(f"Error al actualizar: {e}")

@st.dialog("Registrar Factura")
def dialogo_registrar_factura(estado_app):
    st.markdown("<p class='dialog-title'>Registrar Factura Manual</p>", unsafe_allow_html=True)
    with st.form(key="form_factura"):
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes = st.selectbox("Mes", meses, index=datetime.now().month - 1)
        anio = st.number_input("Año", min_value=2020, max_value=datetime.now().year, value=datetime.now().year)
        consumo_kwh = st.number_input("Consumo (kWh)", min_value=0.0, format="%.2f")
        costo = st.number_input("Costo (ARS $)", min_value=0.0, format="%.2f")

        if st.form_submit_button("Guardar Factura", type="primary", use_container_width=True):
            payload = {
                "id": str(uuid.uuid4()), "mes": mes, "anio": int(anio),
                "consumo_kwh": consumo_kwh, "costo": costo
            }
            try:
                res = requests.post(f"{URL_API}/facturas/{estado_app.usuario_actual}", json=payload)
                res.raise_for_status()
                st.success("Factura guardada.")
                st.cache_data.clear()
                st.rerun()
            except requests.RequestException as e:
                st.error(f"Error al guardar: {e}")