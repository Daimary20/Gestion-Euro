import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3eG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"

if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(URL_SUPABASE, KEY_SUPABASE)

supabase = st.session_state.supabase

st.set_page_config(page_title="EURO Gestión Cloud", layout="wide", page_icon="🏗️")

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
                res = supabase.table("usuarios").select("*").eq("usuario", u).eq("clave", p).execute()
                if res.data:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = u
                    st.rerun()
                else:
                    st.error("Usuario o clave incorrectos")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

    with tab_reg:
        nu = st.text_input("Nuevo Usuario")
        ne = st.text_input("Correo Electrónico")
        np = st.text_input("Contraseña", type="password")
        if st.button("Crear Cuenta"):
            try:
                supabase.table("usuarios").insert({"usuario": nu, "correo": ne, "clave": np}).execute()
                st.success("✅ Registro exitoso. Ahora puedes iniciar sesión.")
            except Exception as e:
                st.error(f"⚠️ Error al registrar: {e}")

    with tab_rec:
        st.subheader("Recuperar Credenciales")
        email_busca = st.text_input("Introduce tu correo electrónico registrado")
        if st.button("Consultar Clave"):
            try:
                res = supabase.table("usuarios").select("*").eq("correo", email_busca).execute()
                if res.data:
                    info = res.data[0]
                    st.info(f"🔑 Tu usuario es: **{info['usuario']}**")
                    st.info(f"🔓 Tu clave es: **{info['clave']}**")
                else:
                    st.warning("Ese correo no está registrado en el sistema
