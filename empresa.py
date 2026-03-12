import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONEXIÓN A SUPABASE ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co" 
# REEMPLAZA CON TU CLAVE sb_publishable REAL
KEY_SUPABASE = "sb_publishable_h7zleHEMdqtAVnEbOjTDJA_fwt_HGNb"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="EURO Gestión Cloud", layout="wide")

# --- CONTROL DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""

# --- PANTALLA DE ACCESO ---
if not st.session_state['autenticado']:
    st.title("🏗️ Sistema EURO Control")
    tab1, tab2, tab3 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse", "📧 Recuperar Acceso"])
    
    with tab1:
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("ENTRAR"):
                res = supabase.table("usuarios").select("*").eq("usuario", u).eq("clave", p).execute()
                if res.data:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = u
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

    with tab2:
        st.subheader("Crear nueva cuenta de técnico")
        with st.form("reg_form"):
            new_u = st.text_input("Nombre de Usuario")
            new_e = st.text_input("Correo Electrónico (Para recuperación)")
            new_p = st.text_input("Contraseña Nueva", type="password")
            confirm_p = st.text_input("Confirmar Contraseña", type="password")
            if st.form_submit_button("REGISTRARME"):
                if new_u and new_e and new_p == confirm_p:
                    try:
                        # Guardamos también el correo en la base de datos
                        supabase.table("usuarios").insert({
                            "usuario": new_u, 
                            "correo": new_e, 
                            "clave": new_p
                        }).execute()
                        st.success("✅ Registro exitoso. Ya puedes Iniciar Sesión.")
                    except:
                        st.error("❌ El usuario ya existe o hubo un error de conexión.")
                else:
                    st.warning("⚠️ Revisa que todos los campos estén llenos y las contraseñas coincidan.")

    with tab3:
        st.subheader("Recuperar Usuario o Contraseña")
        st.info("Introduce tu correo electrónico registrado para recuperar tus credenciales.")
        email_buscar = st.text_input("Correo Electrónico")
        if st.button("BUSCAR MIS DATOS"):
            if email_buscar:
                # Buscamos por correo electrónico
                res = supabase.table("usuarios").select("usuario", "clave").eq("correo", email_buscar).execute()
                if res.data:
                    st.success("✅ Datos encontrados:")
                    st.write(f"**Tu Usuario:** {res.data[0]['usuario']}")
                    st.write(f"**Tu Contraseña:** {res.data[0]['clave']}")
                else:
                    st.error("No se encontró ninguna cuenta asociada a ese correo.")

# --- PANEL PRINCIPAL (DENTRO DEL SISTEMA) ---
else:
    st.sidebar.title(f"👤 {st.session_state['usuario']}")
    opcion = st.sidebar.radio("Menú:", ["📝 Registrar Trabajo", "🔍 Buscador Avanzado", "🚪 Cerrar Sesión"])

    if opcion == "🚪 Cerr
