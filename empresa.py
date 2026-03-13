import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
# Se recomienda limpiar espacios en las credenciales
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3eG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"

# Usamos session_state para mantener la conexión activa
if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(URL_SUPABASE, KEY_SUPABASE)

supabase = st.session_state.supabase

st.set_page_config(page_title="EURO Gestión Cloud", layout="wide", page_icon="🏗️")

# Estado de la sesión
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- 2. LÓGICA DE ACCESO ---
if not st.session_state['autenticado']:
    st.title("🏗️ EURO Control")
    tab_login, tab_reg, tab_rec = st.tabs(["🔐 Iniciar Sesión", "📝 Registro", "📧 Recuperar"])
    
    with tab_login:
        u = st.text_input("Usuario", key="login_u").strip()
        p = st.text_input("Clave", type="password", key="login_p").strip()
        if st.button("Entrar"):
            try:
                res
