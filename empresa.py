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
                    st.warning("Ese correo no está registrado en el sistema.")
            except Exception as e:
                st.error(f"Error al consultar: {e}")

else:
    # --- 3. APP PRINCIPAL (SESIÓN INICIADA) ---
    st.sidebar.title("Menú Principal")
    st.sidebar.write(f"👤 Bienvenido: **{st.session_state['usuario']}**")
    
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    menu = st.sidebar.radio("Navegación:", ["➕ Registrar Reporte", "📋 Ver Historial"])

    # --- MÓDULO: REGISTRAR ---
    if menu == "➕ Registrar Reporte":
        st.header("📝 Nuevo Reporte de Incidencia")
        fecha_auto = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        st.info(f"📅 **Fecha:** {fecha_auto}")

        with st.form("registro_form", clear_on_submit=True):
            eq = st.text_input("Equipo / Maquinaria")
            ar = st.text_input("Área de Trabajo")
            de = st.text_area("Descripción de la novedad")
            f = st.file_uploader("Evidencia (Foto o Video)", type=["jpg","png","jpeg","mp4","mov"])
            
            if st.form_submit_button("Guardar Reporte"):
                if eq and f:
                    try:
                        fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{f.name}"
                        supabase.storage.from_("evidencias").upload(fname, f.getvalue())
                        url = supabase.storage.from_("evidencias").get_public_url(fname)
                        
                        supabase.table("reportes_euro").insert({
                            "fecha": fecha_auto,
                            "tecnico": st.session_state['usuario'],
                            "area": ar, 
                            "equipo": eq, 
                            "descripcion": de, 
                            "url_multimedia": url
                        }).execute()
                        st.success("✅ Reporte enviado correctamente")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.warning("Completa los campos obligatorios y sube un archivo.")

    # --- MÓDULO: HISTORIAL CON BÚSQUEDA ---
    if menu == "📋 Ver Historial":
        st.header("📋 Historial de Reportes")
        
        # --- FILTROS DE BÚSQUEDA ---
        with st.expander("🔍 Buscadores y Filtros", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                f_tecnico = st.text_input("Filtrar por Técnico", placeholder="Ej: Juan")
            with col2:
                f_area = st.text_input("Filtrar por Área", placeholder="Ej: Bodega")
            with col3:
                f_fecha = st.text_input("Filtrar por Fecha", placeholder="Ej: 15/03/2026")

        try:
            res = supabase.table("reportes_euro").select("*").execute()
            if res.data:
                # Invertimos para ver los últimos primero
                reportes = res.data[::-1]

                # Aplicamos lógica de filtros en Python
                if f_tecnico:
                    reportes = [r for r in reportes if f_tecnico.lower() in r['tecnico'].lower()]
                if f_area:
                    reportes = [r for r in reportes if f_area.lower() in r['area'].lower()]
                if f_fecha:
                    reportes = [r for r in reportes if f_fecha in r['fecha']]

                st.write(f"Resultados encontrados: **{len(reportes)}**")
                st.divider()

                for r in reportes:
                    with st.expander(f"📅 {r['fecha']} - ⚙️ {r['equipo']} ({r['tecnico']})"):
                        c1, c2 = st.columns([0.8, 0.2])
                        with c1:
                            st.write(f"**📍 Área:** {r['area']}")
                            st.write(f"**📝 Descripción:** {r['descripcion']}")
                        with c2:
                            if st.button("🗑️ Borrar", key=f"del_{r['id']}"):
                                try:
                                    if r['url_multimedia']:
                                        nombre_archivo = r['url_multimedia'].split("/")[-1]
                                        supabase.storage.from_("evidencias").remove([nombre_archivo])
                                    supabase.table("reportes_euro").delete().eq("id", r['id']).execute()
                                    st.success("Eliminado")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                        # Multimedia
                        url = r['url_multimedia']
                        if url:
                            if any(ext in url.lower() for ext in ['.mp4', '.mov']):
                                st.video(url)
                            else:
                                st.image(url, use_container_width=True)
            else:
                st.info("No hay reportes registrados.")
        except Exception as e:
            st.error(f"Error al cargar historial: {e}")
