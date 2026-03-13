import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- CONEXIÓN ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co" 
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
            except: st.error("Error al buscar.")

else:
    # --- APP PRINCIPAL ---
    st.sidebar.title("Navegación")
    st.sidebar.write(f"👤 Técnico: **{st.session_state['usuario']}**")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    menu = st.sidebar.radio("Ir a:", ["➕ Registrar Reporte", "📋 Historial de Reportes"])

    if menu == "➕ Registrar Reporte":
        st.header("📝 Registrar Nuevo Reporte Técnico")
        
        # Fecha y hora generadas automáticamente
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        st.info(f"📅 **Fecha y Hora actual:** {fecha_actual}")

        with st.form("registro", clear_on_submit=True):
            eq = st.text_input("Equipo / Máquina")
            ar = st.text_input("Área")
            de = st.text_area("Descripción de la novedad")
            
            # Soporte para imágenes y videos
            f = st.file_uploader("Subir Evidencia (Foto o Video)", type=["jpg","png","jpeg","mp4","mov"])
            
            if st.form_submit_button("Guardar y Enviar"):
                if eq and f:
                    try:
                        # 1. Subir al Storage
                        fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{f.name}"
                        supabase.storage.from_("evidencias").upload(fname, f.getvalue())
                        
                        # 2. URL Pública
                        url = supabase.storage.from_("evidencias").get_public_url(fname)
                        
                        # 3. Guardar en Tabla
                        supabase.table("reportes_euro").insert({
                            "fecha": fecha_actual,
                            "tecnico": st.session_state['usuario'],
                            "area": ar, 
                            "equipo": eq, 
                            "descripcion": de, 
                            "url_multimedia": url
                        }).execute()
                        st.success("✅ Reporte guardado con éxito")
                    except Exception as e: 
                        st.error(f"❌ Error al guardar: {e}")
                else: 
                    st.warning("El Equipo y la Evidencia son campos obligatorios.")

    if menu == "📋 Historial de Reportes":
        st.header("📋 Historial de Reportes")
        try:
            res = supabase.table("reportes_euro").select("*").execute()
            if res.data:
                # Mostrar el más reciente arriba
                for r in res.data[::-1]:
                    with st.expander(f"📅 {r['fecha']} - ⚙️ {r['equipo']}"):
                        st.write(f"**Técnico:** {r['tecnico']} | **Área:** {r['area']}")
                        st.write(f"**Descripción:** {r['descripcion']}")
                        
                        # Verificación de multimedia (Imagen o Video)
                        url = r['url_multimedia']
                        if url:
                            ext = url.lower()
                            if ext.endswith(".mp4") or ext.endswith(".mov"):
                                st.video(url)
                            else:
                                st.image(url, use_container_width=True)
            else:
                st.info("Aún no hay reportes en la base de datos.")
        except Exception as e: 
            st.error(f"Error al cargar el historial: {e}")
