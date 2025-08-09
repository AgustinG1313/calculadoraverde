"""
Módulo para centralizar la comunicación con Supabase.
Todas las funciones que realizan peticiones a la base de datos se encuentran aquí.
"""
import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = "https://qhnkkybzcgjbjdepdewc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFobmtreWJ6Y2dqYmpkZXBkZXdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMwOTI2ODIsImV4cCI6MjA2ODY2ODY4Mn0.2p-yyHnBsWDpGpGN-94F10P-Wzn0H_ej5xSSXcb10NQ"


@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def cargar_datos_facturas(user_id):
    try:
        # Validación adicional del UUID
        import uuid
        try:
            uuid.UUID(str(user_id))  # Esto validará el formato UUID
        except ValueError as e:
            st.error(f"ID de usuario inválido: {user_id}")
            return None

        supabase = get_supabase_client()
        response = supabase.from_("facturas") \
                         .select("*") \
                         .eq("usuario_id", user_id) \
                         .execute()
        
        return response.data
    except Exception as e:
        st.error(f"Error al cargar facturas: {str(e)}")
        return None

def cargar_datos_electrodomesticos(username):
    supabase: Client = get_supabase_client()
    response = supabase.table("electrodomesticos").select("*").eq("username", username).execute()
    if response.error:
        st.error(f"Error al cargar electrodomésticos: {response.error.message}")
        return None
    return response.data

def cargar_catalogo_electrodomesticos():
    try:
        supabase = get_supabase_client()
        
        response = supabase.from_("catalogo_electrodomesticos") \
                         .select("*") \
                         .limit(50) \
                         .execute()
        
        return response.data
    except Exception as e:
        st.error(f"Error al cargar catálogo: {str(e)}")
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
        
        # Versión moderna de Supabase maneja los errores diferente
        # Verificamos si hay datos primero
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