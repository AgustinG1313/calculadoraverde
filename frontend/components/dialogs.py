"""
Componentes de UI para todos los diálogos modales de la aplicación.
"""
import streamlit as st
import uuid
from datetime import datetime
from services import api_client
from ocr import *



def process_invoice_sync(file_path: str) -> dict:
    """Versión síncrona para Streamlit"""
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img)
    
    total_kwh = extract_kwh(text)
    desglose = extract_items(text)

    return {
        "total_kwh": total_kwh,
        "desglose": desglose,
        "raw_text": text
    }
    


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
    """Muestra el formulario de resultados del OCR con capacidad de guardado"""
    try:
        with st.spinner("Procesando factura..."):
            # Guardar archivo temporalmente
            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            # Procesar factura
            resultado = process_invoice(tmp_path)
            os.unlink(tmp_path)  # Eliminar archivo temporal

            # Mostrar resultados
            st.success("✅ Factura procesada correctamente")
            
            with st.expander("📄 Datos extraídos", expanded=True):
                col1, col2 = st.columns(2)
                col1.metric("Consumo kWh", resultado.get("total_kwh", 0))
                
                # Mostrar texto OCR
                with col2:
                    raw_text = resultado.get("raw_text", "No se extrajo texto")
                    st.text_area("Texto reconocido", 
                               value="\n".join(raw_text.split("\n")[:10]) + "..." if raw_text else "N/A",
                               height=100)
                
                # Mostrar desglose
                st.subheader("🧾 Desglose de conceptos")
                for item in resultado.get("desglose", []):
                    st.write(f"- **{item.get('concepto', 'Concepto')}**: ${item.get('importe', 0):,.2f}")

            # Botón para guardar (usando la misma estructura que el manual)
            if st.button("💾 Guardar factura", type="primary"):
                meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                
                payload = {
                    "id": str(uuid.uuid4()),
                    "usuario_id": estado_app.usuario_actual_id,  # Usamos estado_app como en el manual
                    "mes": meses[datetime.now().month - 1],  # Mes actual (podría extraerse del OCR)
                    "anio": datetime.now().year,  # Año actual (podría extraerse del OCR)
                    "consumo_kwh": float(resultado.get("total_kwh", 0)),
                    "costo": sum(float(item.get("importe", 0)) for item in resultado.get("desglose", []))
                }
                
                try:
                    supabase = api_client.get_supabase_client()
                    res = supabase.table("facturas").insert(payload).execute()
                    if res.data:
                        st.success("Factura guardada correctamente en la base de datos")
                        st.cache_data.clear()
                        # Limpiar el file uploader
                        if 'ocr_uploader' in st.session_state:
                            del st.session_state.ocr_uploader
                        st.rerun()
                    else:
                        st.error("Error al guardar en la base de datos")
                except Exception as e:
                    st.error(f"Error de conexión con la base de datos: {str(e)}")
                
    except Exception as e:
        st.error(f"❌ Error al procesar la factura: {str(e)}")
        # Limpiar archivo temporal si existe
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