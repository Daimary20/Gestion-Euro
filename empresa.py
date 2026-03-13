import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- CONEXIÓN CONFIGURADA ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co" 
# Aquí he pegado la clave que acabas de enviarme
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3eG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

st.set_page_config(page_title="EURO Gestión Cloud", layout="wide", page_icon="🏗️")

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- LÓGICA DE ACCESO ---
if not st.session_state['autenticado']:
    st.title("🏗️ EURO Control")
    t1, t2, t3 = st.tabs(["🔐 Login", "📝 Registro", "📧 Recuperar"])
    
    with t1:
        u = st.text_input("Usuario", key="login_u")
        p = st.text_input("Clave", type="password", key="login_p")
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
                st.error(f"Error: {e}")

    with t2:
        nu = st.text_input("Nuevo Usuario")
        ne = st.text_input("Correo")
        np = st.text_input("Contraseña", type="password")
        if st.button("Registrarme"):
            try:
                supabase.table("usuarios").insert({"usuario": nu, "correo": ne, "clave": np}).execute()
                st.success("✅ Registro exitoso. Ve a la pestaña Login.")
            except Exception as e: 
                st.error(f"⚠️ Error al registrar: {e}")

    with t3:
        em = st.text_input("Introduce tu correo")
        if st.button("Recuperar"):
            try:
                res = supabase.table("usuarios").select("*").eq("correo", em).execute()
                if res.data:
                    st.info(f"Usuario: {res.data[0]['usuario']} | Clave: {res.data[0]['clave']}")
                else: 
                    st.error("Correo no encontrado")
            except: st.error("Error al buscar.")

else:
    # --- APP PRINCIPAL ---
    st.sidebar.write(f"Sesión: {st.session_state['usuario']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    menu = st.sidebar.radio("Ir a:", ["Registrar", "Historial"])

    if menu == "Registrar":
        st.header("📝 Nuevo Reporte")
        with st.form("registro", clear_on_submit=True):
            eq = st.text_input("Equipo")
            ar = st.text_input("Área")
            de = st.text_area("Descripción")
            f = st.file_uploader("Evidencia", type=["jpg","png","jpeg","mp4"])
            if st.form_submit_button("Guardar"):
                if eq and f:
                    try:
                        fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{f.name}"
                        supabase.storage.from_("evidencias").upload(fname, f.getvalue())
                        url = supabase.storage.from_("evidencias").get_public_url(fname)
                        
                        supabase.table("reportes_euro").insert({
                            "fecha": datetime.now().strftime("%d/%m/%Y"),
                            "tecnico": st.session_state['usuario'],
                            "area": ar, "equipo": eq, "descripcion": de, "url_multimedia": url
                        }).execute()
                        st.success("✅ Guardado correctamente")
                    except Exception as e: 
                        st.error(f"Error al guardar: {e}")
                else: st.error("Faltan datos obligatorios.")

    if menu == "Historial":
        st.header("📋 Historial")
        try:
            res = supabase.table("reportes_euro").select("*").execute()
            if res.data:
                for r in res.data[::-1]:
                    with st.expander(f"{r['fecha']} - {r['equipo']}"):
                        st.write(f"Técnico: {r['tecnico']} | Área: {r['area']}")
                        st.write(r['descripcion'])
                        if r['url_multimedia']:
                            if r['url_multimedia'].lower().endswith('.mp4'): 
                                st.video(r['url_multimedia'])
                            else: 
                                st.image(r['url_multimedia'], use_container_width=True)
            else:
                st.info("No hay reportes aún.")
        except Exception as e: 
            st.warning(f"Error al cargar: {e}")
