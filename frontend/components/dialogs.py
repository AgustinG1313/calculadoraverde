"""
Componentes de UI para todos los diálogos modales de la aplicación.
"""
from pdf2image import convert_from_path
import os
import streamlit as st
import uuid
from datetime import datetime
from services import api_client
from ocr import *
import re 
from PIL import Image

#POPPLER_PATH = r"C:\Release-24.08.0-0\poppler-24.08.0\Library\bin"   


def process_invoice_sync(file_path: str) -> dict:
    """Procesa facturas SECHEEP conservando el formato original"""
    try:
        # Configuración de Poppler (asegúrate de que la ruta sea correcta)
        POPPLER_PATH = r"C:\Release-24.08.0-0\poppler-24.08.0\Library\bin"
        
        # Cargar archivo (PDF o imagen)
        if file_path.lower().endswith('.pdf'):
            images = convert_from_path(
                file_path,
                first_page=1,
                last_page=1,
                dpi=300,
                poppler_path=POPPLER_PATH
            )
            img = images[0] if images else None
        else:
            img = Image.open(file_path)
        
        if not img:
            raise ValueError("No se pudo cargar el archivo")

        # Preprocesamiento para OCR (sin eliminar espacios)
        img = img.convert('L')  # Escala de grises
        text = pytesseract.image_to_string(img, config='--psm 6')

        # Debug: Mostrar texto exacto (conservando espacios y saltos de línea)
        print("=== TEXTO ORIGINAL ===")
        print(repr(text))  # Muestra caracteres ocultos como \n, \t, etc.

        # ---- Extracción de CONSUMO (kWh) ----
        consumo_match = re.search(
            r"Kwh\s+(\d+\.\d{2})\s+0\.00\s+0\.00",  # Busca "Kwh 272.00 0.00 0.00"
            text
        )
        consumo_kwh = float(consumo_match.group(1)) if consumo_match else 0.0

        # ---- Extracción de TOTAL ($35,208.96) ----
        # Busca "Total Vto al 01/09/25 1° Vto $ 35,208.96" (con espacios)
        total_match = re.search(
            r"1°\s+Vto\s*\$\s*([\d\.,]+)",
            text
        )
        if total_match:
            costo_total = float(total_match.group(1).replace(",", ""))
        else:
            costo_total = 0.0

        # ---- Extracción de PERÍODO (06/2025) ----
        periodo_match = re.search(r"Per[ií]odo:\s*(\d{2})/(\d{4})", text)
        if periodo_match:
            mes_num = int(periodo_match.group(1))
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes = meses[mes_num - 1]
            anio = int(periodo_match.group(2))
        else:
            mes = datetime.now().strftime("%B")
            anio = datetime.now().year

        return {
            "total_kwh": consumo_kwh,
            "costo_total": costo_total,
            "mes": mes,
            "anio": anio,
            "raw_text": text  # Texto original para diagnóstico
        }

    except Exception as e:
        raise ValueError(f"Error al procesar: {str(e)}")
    
@st.dialog("Subir Factura (OCR)")
def dialogo_subir_ocr(estado_app):
    """Muestra el uploader de archivos OCR con acceso al estado"""
    # Verificar autenticación
    if not hasattr(estado_app, 'usuario_actual_id') or not estado_app.usuario_actual_id:
        st.error("🔒 Debes iniciar sesión para subir facturas")
        return
    
    uploaded_file = st.file_uploader(
        "Arrastra tu archivo o haz clic para buscar", 
        type=["pdf", "png", "jpg", "jpeg"], 
        key="ocr_uploader"
    )
    
    if uploaded_file is not None:
        mostrar_formulario_ocr(uploaded_file, estado_app)
    else:
        st.info("📌 Sube una imagen o PDF de tu factura para extraer la información automáticamente")

def mostrar_formulario_ocr(uploaded_file, estado_app):
    try:
        with st.spinner("Procesando factura..."):
            # Guardar archivo temporal
            suffix = uploaded_file.name.split('.')[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{suffix}') as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            # Procesar
            resultado = process_invoice_sync(tmp_path)
            os.unlink(tmp_path)

            # --- Mostrar resultados ---
            st.success("✅ Datos extraídos")
            
            cols = st.columns(2)
            cols[0].metric("Consumo kWh", f"{resultado['total_kwh']:.2f}")
            cols[1].metric("Total a pagar", f"${resultado['costo_total']:,.2f}")
            
            st.write(f"**Período:** {resultado['mes']} {resultado['anio']}")
            
            # Botón de guardado
            if st.button("💾 Guardar factura", type="primary"):
                payload = {
                    "id": str(uuid.uuid4()),
                    "usuario_id": estado_app.usuario_actual_id,
                    "mes": resultado["mes"],
                    "anio": resultado["anio"],
                    "consumo_kwh": resultado["total_kwh"],
                    "costo": resultado["costo_total"]
                }
                
                try:
                    supabase = api_client.get_supabase_client()
                    res = supabase.table("facturas").insert(payload).execute()
                    if res.data:
                        st.success("¡Factura guardada en la base de datos!")
                        st.cache_data.clear()
                        if 'ocr_uploader' in st.session_state:
                            del st.session_state.ocr_uploader
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {str(e)}")
                    
    except Exception as e:
        st.error(f"❌ Error crítico: {str(e)}")
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
            
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
                "id": str(uuid.uuid4()),
                "usuario_id": estado_app.usuario_actual_id,
                "nombre": nombre_aparato,
                "cantidad": cantidad,
                "potencia": potencia,
                "eficiencia": "A",
                "horas_dia": horas_dia,
                "dias_mes": dias_mes
            }
            try:
                supabase = api_client.get_supabase_client()
                res = supabase.table("electrodomesticos").insert(payload).execute()
                if res.data:
                    st.success("Electrodoméstico añadido.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Error al añadir electrodoméstico.")
            except Exception as e:
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
                "cantidad": cantidad,
                "potencia": potencia,
                "horas_dia": horas_dia,
                "dias_mes": dias_mes
            }
            try:
                supabase = api_client.get_supabase_client()
                res = supabase.table("electrodomesticos").update(payload).eq("id", aparato["id"]).execute()
                if res.data:
                    st.success("Electrodoméstico actualizado.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Error al actualizar electrodoméstico.")
            except Exception as e:
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
                "id": str(uuid.uuid4()),
                "usuario_id": estado_app.usuario_actual_id,
                "mes": mes,
                "anio": int(anio),
                "consumo_kwh": consumo_kwh,
                "costo": costo
            }
            try:
                supabase = api_client.get_supabase_client()
                res = supabase.table("facturas").insert(payload).execute()
                if res.data:
                    st.success("Factura guardada.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Error al guardar factura.")
            except Exception as e:
                st.error(f"Error al guardar: {e}")