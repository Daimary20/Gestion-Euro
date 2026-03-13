import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- CONEXIÓN (Se recomienda usar st.secrets para producción) ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co" 
KEY_SUPABASE = "TU_API_KEY_AQUÍ" # Reemplaza con tu clave real

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

st.set_page_config(page_title="EURO Gestión Cloud", layout="wide", page_icon="🏗️")

# Inicialización de estado de sesión
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
            except: 
                st.error("⚠️ Error: El usuario/correo ya existe o falta configurar SQL.")

    with t3:
        em = st.text_input("Introduce tu correo")
        if st.button("Recuperar"):
            try:
                res = supabase.table("usuarios").select("usuario, clave").eq("correo", em).execute()
                if res.data:
                    st.info(f"Usuario: {res.data[0]['usuario']} | Clave: {res.data[0]['clave']}")
                else: 
                    st.error("Correo no encontrado")
            except: 
                st.error("Error al buscar en la base de datos.")

else:
    # --- APP PRINCIPAL ---
    st.sidebar.title(f"Bienvenido")
    st.sidebar.write(f"👤 {st.session_state['usuario']}")
    
    menu = st.sidebar.radio("Navegación:", ["Registrar Reporte", "Historial de Reportes"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    if menu == "Registrar Reporte":
        st.header("📝 Nuevo Reporte Técnico")
        with st.form("registro", clear_on_submit=True):
            eq = st.text_input("Equipo / Maquinaria")
            ar = st.text_input("Área de Trabajo")
            de = st.text_area("Descripción de la novedad")
            f = st.file_uploader("Subir Evidencia (Imagen o Video)", type=["jpg","png","jpeg","mp4"])
            
            enviar = st.form_submit_button("Guardar Reporte")
            
            if enviar:
                if eq and f:
                    try:
                        # 1. Subir archivo al Storage
                        fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{f.name}"
                        supabase.storage.from_("evidencias").upload(fname, f.getvalue())
                        
                        # 2. Obtener URL pública
                        url = supabase.storage.from_("evidencias").get_public_url(fname)
                        
                        # 3. Guardar en base de datos
                        supabase.table("reportes_euro").insert({
                            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "tecnico": st.session_state['usuario'],
                            "area": ar, 
                            "equipo": eq, 
                            "descripcion": de, 
                            "url_multimedia": url
                        }).execute()
                        st.success("✅ Reporte guardado exitosamente.")
                    except Exception as e: 
                        st.error(f"Error al guardar: {e}")
                else: 
                    st.warning("El nombre del equipo y la evidencia son obligatorios.")

    if menu == "Historial":
        st.header("📋 Historial de Reportes")
        try:
            res = supabase.table("reportes_euro").select("*").order("creado_at", desc=True).execute()
            if not res.data:
                st.info("No hay reportes registrados.")
            
            for r in res.data:
                with st.expander(f"📅 {r['fecha']} - ⚙️ {r['equipo']}"):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.write(f"**Técnico:** {r['tecnico']}")
                        st.write(f"**Área:** {r['area']}")
                        st.write(f"**Descripción:** {r['descripcion']}")
                    with col2:
                        if r['url_multimedia']:
                            if r['url_multimedia'].lower().endswith('.mp4'):
                                st.video(r['url_multimedia'])
                            else:
                                st.image(r['url_multimedia'], use
