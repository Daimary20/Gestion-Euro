import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONEXIÓN A SUPABASE ---
# Encuentra estos datos en: Settings -> API en tu panel de Supabase
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co" 
KEY_SUPABASE = "sb_publishable_h7zleHEMdqtAVnEbOjTDJA_fwt_HGNb"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="EURO Gestión Cloud", layout="wide")

# Estilo para mejorar la visualización
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CONTROL DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""

# --- PANTALLA DE ACCESO ---
if not st.session_state['autenticado']:
    st.title("🏗️ Sistema EURO Control")
    tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
    
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
        st.subheader("Crear nueva cuenta")
        with st.form("reg_form"):
            new_u = st.text_input("Nombre de Usuario")
            new_p = st.text_input("Contraseña Nueva", type="password")
            confirm_p = st.text_input("Confirmar Contraseña", type="password")
            if st.form_submit_button("REGISTRAR"):
                if new_u and new_p == confirm_p:
                    try:
                        supabase.table("usuarios").insert({"usuario": new_u, "clave": new_p}).execute()
                        st.success("✅ Cuenta creada. Ya puedes iniciar sesión.")
                    except:
                        st.error("❌ El usuario ya existe.")
                else:
                    st.warning("⚠️ Datos inválidos o contraseñas no coinciden.")

# --- PANEL PRINCIPAL ---
else:
    st.sidebar.title(f"👤 {st.session_state['usuario']}")
    opcion = st.sidebar.radio("Menú:", ["📝 Registrar Trabajo", "🔍 Buscador Avanzado", "🚪 Salir"])

    if opcion == "🚪 Salir":
        st.session_state['autenticado'] = False
        st.rerun()

    elif opcion == "📝 Registrar Trabajo":
        st.header("📝 Nuevo Reporte de Actividad")
        
        with st.form("form_trabajo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            area = col1.text_input("📍 Área / Ubicación")
            equipo = col2.text_input("📦 Equipo / Máquina")
            
            col3, col4 = st.columns(2)
            fec = col3.date_input("📅 Fecha", datetime.now())
            hor = col4.time_input("🕒 Hora", datetime.now())
            
            desc = st.text_area("📝 Descripción detallada")
            archivo = st.file_uploader("📷 Adjuntar Foto o Video", type=["jpg", "png", "jpeg", "mp4"])
            
            if st.form_submit_button("GUARDAR REPORTE"):
                if equipo and archivo:
                    # 1. Subir archivo a Storage (Bucket 'evidencias')
                    file_ext = archivo.name.split(".")[-1]
                    file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                    
                    supabase.storage.from_("evidencias").upload(file_name, archivo.getvalue())
                    url_file = supabase.storage.from_("evidencias").get_public_url(file_name)
                    
                    # 2. Guardar datos en Tabla
                    datos = {
                        "fecha": fec.strftime("%d/%m/%Y"),
                        "hora": hor.strftime("%H:%M"),
                        "tecnico": st.session_state['usuario'],
                        "area": area,
                        "equipo": equipo,
                        "descripcion": desc,
                        "url_multimedia": url_file
                    }
                    supabase.table("reportes_euro").insert(datos).execute()
                    st.success("✅ Guardado en la nube con éxito.")
                    st.balloons()
                else:
                    st.error("⚠️ El equipo y el archivo son obligatorios.")

    elif opcion == "🔍 Buscador Avanzado":
        st.header("🔍 Historial de Actividades")
        res = supabase.table("reportes_euro").select("*").execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            busqueda = st.text_input("🔍 Filtrar reportes...")
            
            if busqueda:
                df = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
            
            for _, row in df.iloc[::-1].iterrows():
                with st.expander(f"📋 {row['fecha']} | {row['tecnico']} | {row['equipo']}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.write(f"**🕒 Hora:** {row['hora']}")
                        st.write(f"**📍 Área:** {row['area']}")
                        st.write(f"**📝 Descripción:** {row['descripcion']}")
                    with c2:
                        url = row['url_multimedia']
                        if url.lower().endswith('.mp4'):
                            st.video(url)
                        else:
                            st.image(url, use_container_width=True)
        else:
            st.info("No hay registros todavía.")

