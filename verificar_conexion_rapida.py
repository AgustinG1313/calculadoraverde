from supabase import create_client, Client

SUPABASE_URL = "https://qhnkkybzcgjbjdepdewc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFobmtreWJ6Y2dqYmpkZXBkZXdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMwOTI2ODIsImV4cCI6MjA2ODY2ODY4Mn0.2p-yyHnBsWDpGpGN-94F10P-Wzn0H_ej5xSSXcb10NQ"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def verificar_conexion_supabase():
    try:
        resp = supabase.table("usuarios").select("*").limit(1).execute()
        # Verifica si la respuesta tiene datos
        if hasattr(resp, "data") and resp.data is not None:
            print("Conexión exitosa a Supabase.")
            return True
        else:
            print("No se pudo obtener datos. Puede que la tabla esté vacía o haya un error de conexión.")
            return False
    except Exception as e:
        import traceback
        print("Excepción al conectar:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verificar_conexion_supabase()