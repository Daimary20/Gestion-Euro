import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONEXIÓN A LA BASE DE DATOS (REEMPLAZA CON TUS DATOS) ---
# Busca estos datos en Supabase: Settings -> API
URL_SUPABASE = "https://tu-proyecto.supabase.co" 
KEY_SUPABASE = "tu-clave-anon-public-aqui"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="EURO Gestión Cloud", layout="wide")

# --- CONTROL DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""

# --- PANTALLA DE ACCESO (LOGIN Y REGISTRO) ---
if not st.session_state['autenticado']:
    st.title("🏗️ Sistema EURO Control")
    tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrar Nuevo Técnico"])
    
    with tab1:
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("ENTRAR"):
                # Verificamos credenciales en la tabla 'usuarios'
                res = supabase.table("usuarios").select("*").eq("usuario", u).eq("clave", p).execute()
                if res.data:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = u
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

    with tab2:
        st.subheader("Crea tu cuenta")
        with st.form("reg_form"):
            new_u = st.text_input("Nombre de Usuario")
            new_p = st.text_input("Contraseña Nueva", type="password")
            confirm_p = st.text_input("Repetir Contraseña", type="password")
            if st.form_submit_button("REGISTRARME"):
                if new_u and new_p == confirm_p:
                    # Insertamos en la tabla 'usuarios'
                    try:
                        supabase.table("usuarios").insert({"usuario": new_u, "clave": new_p}).execute()
                        st.success("✅ Cuenta creada con éxito. Ya puedes iniciar sesión.")
                    except:
                        st.error("❌ El usuario ya existe o hubo un error.")
                else:
                    st.warning("⚠️ Las contraseñas no coinciden o faltan datos.")

# --- PANEL PRINCIPAL (USUARIO LOGUEADO) ---
else:
    st.sidebar.title(f"👤 {st.session_state['usuario']}")
    opcion = st.sidebar.radio("Menú:", ["📝 Registrar Trabajo", "🔍 Buscador Avanzado", "🚪 Cerrar Sesión"])

    if opcion == "🚪 Cerrar Sesión":
        st.session_state['autenticado'] = False
        st.rerun()

    # --- OPCIÓN: REGISTRAR TRABAJO ---
    elif opcion == "📝 Registrar Trabajo":
        st.header("📝 Nuevo Reporte de Actividad")
        st.info(f"Técnico responsable: **{st.session_state['usuario']}**")
        
        with st.form("form_trabajo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            area = col1.text_input("📍 Área / Ubicación")
            equipo = col2.text_input("📦 Equipo / Máquina")
            
            col3, col4 = st.columns(2)
            fec = col3.date_input("📅 Fecha", datetime.now())
            hor = col4.time_input("🕒 Hora", datetime.now())
            
            desc = st.text_area("📝 Descripción detallada")
            archivo = st.file_uploader("📷 Adjuntar Evidencia (Foto o Video)", type=["jpg", "png", "jpeg", "mp4"])
            
            if st.form_submit_button("GUARDAR REPORTE"):
                if equipo and archivo:
                    # 1. Subir el archivo al Storage (bucket 'evidencias')
                    file_ext = archivo.name.split(".")[-1]
                    file_name = f"{st.session_state['usuario']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                    
                    supabase.storage.from_("evidencias").upload(file_name, archivo.getvalue())
                    url_file = supabase.storage.from_("evidencias").get_public_url(file_name)
                    
                    # 2. Guardar datos en la tabla 'reportes_euro'
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
                    st.success("✅ Reporte guardado permanentemente en la nube.")
                    st.balloons()
                else:
                    st.error("⚠️ El equipo y el archivo multimedia son obligatorios.")

    # --- OPCIÓN: BUSCADOR AVANZADO ---
    elif opcion == "🔍 Buscador Avanzado":
        st.header("🔍 Historial de Actividades")
        # Traer datos desde Supabase
        res = supabase.table("reportes_euro").select("*").execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            busqueda = st.text_input("🔍 Filtrar por cualquier campo...")
            
            if busqueda:
                df = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
            
            # Mostrar los más recientes primero
            for _, row in df.iloc[::-1].iterrows():
                with st.expander(f"📋 {row['fecha']} | {row['tecnico']} | {row['equipo']}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.write(f"**🕒 Hora:** {row['hora']}")
                        st.write(f"**📍 Área:** {row['area']}")
                        st.write(f"**📝 Descripción:** {row['descripcion']}")
                    with c2:
                        if row['url_multimedia'].lower().endswith('.mp4'):
                            st.video(row['url_multimedia'])
                        else:
                            st.image(row['url_multimedia'], use_container_width=True)
        else:
            st.info("No hay registros en la base de datos.")
