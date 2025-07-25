"""
Componente de UI para la barra de navegación principal.
"""
import streamlit as st

def cambiar_pagina(pagina):
    st.session_state.estado.pagina_actual = pagina

def mostrar_barra_navegacion():
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
            st.button(
                label,
                key=f"nav_{key}",
                on_click=cambiar_pagina,
                args=(key,),
                use_container_width=True
            )
    st.markdown('</div>', unsafe_allow_html=True)