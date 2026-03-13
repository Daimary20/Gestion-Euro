import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# --- CONEXIÓN ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co" 
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3eG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

st.set_page_config(page_title="EURO Gestión Cloud", layout="wide")

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- ACCESO ---
if not st.session_state['autenticado']:
    st.title("🏗️ EURO Control")
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Registro"])
    
    with tab1:
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            res = supabase.table("usuarios").select("*").eq("usuario", u).eq("clave", p).execute()
            if res.data:
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = u
                st.rerun()
            else: st.error("Datos incorrectos")

    with tab2:
        nu = st.text_input("Nuevo Usuario")
        ne = st.text_input("Correo")
        np = st.text_input("Contraseña", type="password")
        if st.button("Registrarme"):
            supabase.table("usuarios").insert({"usuario": nu, "correo": ne, "clave": np}).execute()
            st.success("✅ Registrado. Ve a Login.")

else:
    # --- APP PRINCIPAL ---
    st.sidebar.write(f"👤 Técnico: {st.session_state['usuario']}")
    menu = st.sidebar.radio("Menú", ["Registrar Reporte", "Historial"])

    if menu == "Registrar Reporte":
        st.header("📝 Nuevo Reporte")
        # FECHA Y HORA AUTOMÁTICA
        ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        st.write(f"📅 **Fecha:** {ahora}")

        with st.form("form_reporte", clear_on_submit=True):
            equipo = st.text_input("Equipo")
            area = st.text_input("Área")
            desc = st.text_area("Descripción")
            archivo = st.file_uploader("Evidencia (Imagen o Video)", type=["jpg","png","mp4","mov"])
            
            if st.form_submit_button("Guardar"):
                if equipo and archivo:
                    try:
                        # Subir al storage
                        nombre_f = f"{datetime.now().strftime('%H%M%S')}_{archivo.name}"
                        supabase.storage.from_("evidencias").upload(nombre_f, archivo.getvalue())
                        url_pub = supabase.storage.from_("evidencias").get_public_url(nombre_f)
                        
                        # Guardar en tabla
                        supabase.table("reportes_euro").insert({
                            "fecha": ahora,
                            "tecnico": st.session_state['usuario'],
                            "area": area,
                            "equipo": equipo,
                            "descripcion": desc,
                            "url_multimedia": url_pub
                        }).execute()
                        st.success("✅ Reporte guardado con éxito")
                    except Exception as e: st.error(f"Error: {e}")
                else: st.warning("Completa los campos y sube un archivo.")

    if menu == "Historial":
        st.header("📋 Historial")
        res = supabase.table("reportes_euro").select("*").execute()
        for r in res.data[::-1]:
            with st.expander(f"{r['fecha']} - {r['equipo']}"):
                st.write(f"**Técnico:** {r['tecnico']} | **Área:** {r['area']}")
                st.write(r['descripcion'])
                url = r['url_multimedia']
                if url:
                    # REPRODUCTOR DE VIDEO O IMAGEN
                    if url.lower().endswith(('.mp4', '.mov')):
                        st.video(url)
                    else:
                        st.image(url, use_container_width=True)
