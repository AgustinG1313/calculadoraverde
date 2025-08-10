"""
Módulo para centralizar la comunicación con Supabase.
Todas las funciones que realizan peticiones a la base de datos se encuentran aquí.
"""
import streamlit as st
from supabase import create_client, Client
import uuid



SUPABASE_URL = "https://qhnkkybzcgjbjdepdewc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFobmtreWJ6Y2dqYmpkZXBkZXdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMwOTI2ODIsImV4cCI6MjA2ODY2ODY4Mn0.2p-yyHnBsWDpGpGN-94F10P-Wzn0H_ej5xSSXcb10NQ"

def eliminar_electrodomestico(electrodomestico_id: str):
    """Elimina un electrodoméstico por su ID"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("electrodomesticos")\
                         .delete()\
                         .eq("id", electrodomestico_id)\
                         .execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error al eliminar electrodoméstico: {str(e)}")
        return False
    
def calcular_huella_carbono(consumo_kwh: float) -> float:
    """
    Calcula la huella de carbono en kg de CO2 basado en el consumo eléctrico.
    
    Args:
        consumo_kwh: Consumo eléctrico en kilowatt-hora
        
    Returns:
        float: Huella de carbono en kilogramos de CO2 equivalente
    
    Nota:
        El factor de emisión puede variar según la región.
        Este ejemplo usa 0.5 kg CO2/kWh como valor por defecto.
    """
    FACTOR_EMISION_CO2 = 0.5  # kg CO2 por kWh (ajusta este valor según tu región)
    return consumo_kwh * FACTOR_EMISION_CO2    
    
    
    
def calcular_costo_rango(consumo_kwh: float, nivel_subsidio: str = "medio") -> float:
    """
    Calcula el costo estimado basado en el consumo y nivel de subsidio.
    Valores de ejemplo para Argentina (ajusta según tus necesidades):
    - Bajo subsidio: $50 por kWh
    - Medio subsidio: $30 por kWh
    - Alto subsidio: $10 por kWh
    """
    tarifas = {
        "bajo": 50.0,
        "medio": 30.0,
        "alto": 10.0
    }
    
    # Asegúramos que el nivel de subsidio esté en minúsculas
    nivel_subsidio = nivel_subsidio.lower()
    
    # Obtenemos la tarifa o usamos la media por defecto si no existe
    tarifa = tarifas.get(nivel_subsidio, 30.0)
    
    return consumo_kwh * tarifa

    
def cargar_datos_electrodomesticos(usuario_id: str):
    """Carga los electrodomésticos de un usuario desde Supabase"""
    try:
        # Validación del UUID
        uuid.UUID(str(usuario_id))
    except ValueError as e:
        st.error(f"ID de usuario inválido: {usuario_id}")
        return None

    try:
        supabase = get_supabase_client()
        response = supabase.table("electrodomesticos")\
                         .select("*")\
                         .eq("usuario_id", usuario_id)\
                         .execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        st.error(f"Error al cargar electrodomésticos: {str(e)}")
        return None

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def cargar_datos_facturas(user_id):
    try:
        # Validación del UUID
        uuid.UUID(str(user_id))
    except ValueError as e:
        st.error(f"ID de usuario inválido: {user_id}")
        return None

    try:
        supabase = get_supabase_client()
        response = supabase.from_("facturas") \
                     .select("id, mes, anio, consumo_kwh, costo").eq("usuario_id", user_id).order("anio", desc=True).execute()

        if not response.data:
            return []

        # Verificación de estructura
        required_keys = {'mes', 'anio', 'consumo_kwh', 'costo'}
        if not all(key in response.data[0] for key in required_keys):
            st.error("Estructura de facturas incorrecta")
            return None

        return response.data
    except Exception as e:
        st.error(f"Error al cargar facturas: {str(e)}")
        return None
        
    except Exception as e:
        st.error(f"Error al cargar facturas: {str(e)}")
        return None
  
  
    
    


def cargar_catalogo_electrodomesticos():
    try:
        supabase = get_supabase_client()
        
        # Intenta cargar el catálogo directamente
        response = supabase.from_("catalogo_electrodomesticos") \
                         .select("*") \
                         .order("nombre") \
                         .execute()
        
        # Verifica si la respuesta contiene el error de tabla no encontrada
        if hasattr(response, 'error') and response.error:
            if "relation \"catalogo_electrodomesticos\" does not exist" in str(response.error):
                st.error("La tabla de catálogo no existe en la base de datos")
                return []
            else:
                raise Exception(response.error.message)
        
        if not response.data:
            st.warning("El catálogo está vacío. Por favor, añade electrodomésticos al catálogo.")
            return []
            
        return response.data
        
    except Exception as e:
        st.error(f"Error al cargar catálogo: {str(e)}")
        print(f"Error completo: {e}")  # Para depuración
        return []
    
@st.cache_data(ttl=60)
def cargar_metricas_resumen(user_id):
    try:
        supabase = get_supabase_client()
        
        # Versión actualizada para Supabase v2+
        response = supabase.from_("metricas_resumen") \
                         .select("*") \
                         .eq("usuario_id", user_id) \
                         .execute()
        
        # La respuesta ahora es un objeto con .data y .count
        if not response.data:
            st.warning("No se encontraron métricas para este usuario")
            return None
            
        return response.data[0]  # Devuelve el primer registro
        
    except Exception as e:
        st.error(f"Error al cargar métricas: {str(e)}")
        print(f"Error completo: {e}")  # Para depuración
        return None

@st.cache_data(ttl=60)
def cargar_metricas_perfil(user_id):
    try:
        supabase = get_supabase_client()
        response = supabase.table("cargar_metricas_perfil")\
                         .select("*")\
                         .eq("id", user_id)\
                         .single()\
                         .execute()
        
        
        if not response.data:
            st.warning("No se encontraron datos para el usuario")
            return None
            
        return response.data
        
    except Exception as e:
        st.error(f"Error al cargar métricas: {str(e)}")
        return None
@st.cache_data(ttl=60)
def cargar_consejos(user_id):
    try:
        supabase = get_supabase_client()
        response = supabase.from_("vista_consejos_personalizados") \
                         .select("*") \
                         .eq("usuario_id", user_id) \
                         .execute()
        
        return response.data or []  # Retorna lista vacía si no hay datos
        
    except Exception as e:
        st.error(f"Error al cargar consejos: {str(e)}")
        return []

def marcar_consejo_cumplido(user_id, consejo_id):
    supabase: Client = get_supabase_client()
    response = supabase.table("consejos_cumplidos").insert({
        "user_id": user_id,
        "consejo_id": consejo_id
    }).execute()
    if response.error:
        st.error(f"Error al marcar consejo cumplido: {response.error.message}")
        return None
    return response.data