import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- CONEXIÓN ---
# Nota: Asegúrate de que estas credenciales sean las correctas de tu proyecto
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co" 
KEY_SUPABASE = "sb_publishable_h7zleHEMdqtAvnEbOjTDJA_fwt_HId_I0u9Xf9m9n0-Qy9V8g7rX-E_h-YJ_H0_jL"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

st.set_page_config(page_title="EURO Gestión Cloud", layout="wide", page_icon="🏗️")

# Inicialización del estado de la sesión
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
                st.error(f"Error de conexión: {e}")

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
            except Exception as e: 
                st.error(f"Error al buscar: {e}")

else:
    # --- APP PRINCIPAL ---
    st.sidebar.title("Navegación")
    st.sidebar.write(f"👤 Sesión: **{st.session_state['usuario']}**")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    menu = st.sidebar.radio("Ir a:", ["Registrar", "Historial"])

    if menu == "Registrar":
        st.header("📝 Registrar Nuevo Reporte")
        with st.form("registro", clear_on_submit=True):
            eq = st.text_input("Equipo")
            ar = st.text_input("Área")
            de = st.text_area("Descripción")
            f = st.file_uploader("Evidencia", type=["jpg","png","jpeg","mp4"])
            
            if st.form_submit_button("Guardar"):
                if eq and f:
                    try:
                        # Subir archivo al Storage
                        fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{f.name}"
                        supabase.storage.from_("evidencias").upload(fname, f.getvalue())
                        
                        # Obtener URL pública
                        url = supabase.storage.from_("evidencias").get_public_url(fname)
                        
                        # Insertar en la tabla reportes_euro
                        supabase.table("reportes_euro").insert({
                            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "tecnico": st.session_state['usuario'],
                            "area": ar, 
                            "equipo": eq, 
                            "descripcion": de, 
                            "url_multimedia": url
                        }).execute()
                        st.success("✅ Reporte guardado correctamente")
                    except Exception as e: 
                        st.error(f"Error al guardar: {e}")
                else: 
                    st.error("Por favor, completa el nombre del equipo y sube una evidencia.")

    if menu == "Historial":
        st.header("📋 Historial de Reportes")
        try:
            res = supabase.table("reportes_euro").select("*").execute()
            if res.data:
                for r in res.data[::-1]:
                    with st.expander(f"📅 {r['fecha']} - ⚙️ {r['equipo']}"):
                        st.write(f"**Técnico:** {r['tecnico']} | **Área:** {r['area']}")
                        st.write(f"**Descripción:** {r['descripcion']}")
                        
                        url = r['url_multimedia']
                        if url:
                            if url.lower().endswith('.mp4'): 
                                st.video(url)
                            else: 
                                # Aquí corregimos el error del paréntesis
                                st.image(url, use_container_width=True)
            else:
                st.info("No hay reportes registrados todavía.")
        except Exception as e: 
            st.warning(f"No se pudieron cargar los reportes: {e}")
