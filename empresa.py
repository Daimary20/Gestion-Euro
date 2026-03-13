import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# --- CONEXIÓN ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co" 
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3eG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

st.set_page_config(page_title="EURO Gestión Cloud", layout="wide", page_icon="🏗️")

# Estado de autenticación
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- LÓGICA DE ACCESO (LOGIN / REGISTRO) ---
if not st.session_state['autenticado']:
    st.title("🏗️ EURO Control")
    tab_login, tab_reg = st.tabs(["🔐 Iniciar Sesión", "📝 Registro"])
    
    with tab_login:
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

else:
    # --- APP PRINCIPAL ---
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
                        # 1. Subir al Storage (Bucket: evidencias)
                        fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{f.name}"
                        supabase.storage.from_("evidencias").upload(fname, f.getvalue())
                        url = supabase.storage.from_("evidencias").get_public_url(fname)
                        
                        # 2. Guardar en Base de Datos
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
                    st.warning("Completa los campos obligatorios.")

    # --- MÓDULO: HISTORIAL CON BORRADO ---
    if menu == "📋 Ver Historial":
        st.header("📋 Historial de Reportes")
        try:
            res = supabase.table("reportes_euro").select("*").execute()
            if res.data:
                for r in res.data[::-1]:
                    with st.expander(f"📅 {r['fecha']} - ⚙️ {r['equipo']}"):
                        col_info, col_del = st.columns([0.85, 0.15])
                        
                        with col_info:
                            st.write(f"**Técnico:** {r['tecnico']} | **Área:** {r['area']}")
                            st.write(f"**Descripción:** {r['descripcion']}")
                        
                        with col_del:
                            # BOTÓN DE ELIMINAR
                            if st.button("🗑️ Borrar", key=f"btn_{r['id']}"):
                                # A. Borrar archivo del Storage
                                if r['url_multimedia']:
                                    try:
                                        nombre_archivo = r['url_multimedia'].split("/")[-1]
                                        supabase.storage.from_("evidencias").remove([nombre_archivo])
                                    except: pass # Si el archivo ya no existe, ignorar
                                
                                # B. Borrar registro de la tabla
                                supabase.table("reportes_euro").delete().eq("id", r['id']).execute()
                                st.success("Eliminado")
                                st.rerun()

                        # VISUALIZACIÓN MULTIMEDIA
                        url = r['url_multimedia']
                        if url:
                            if any(ext in url.lower() for ext in ['.mp4', '.mov']):
                                st.video(url)
                            else:
                                st.image(url, use_container_width=True)
            else:
                st.info("No hay reportes registrados.")
        except Exception as e:
            st.error(f"Error al cargar: {e}")
