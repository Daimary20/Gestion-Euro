import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONEXIÓN A SUPABASE ---
# REEMPLAZA CON TUS DATOS REALES DE SUPABASE
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co" 
KEY_SUPABASE = "sb_publishable_h7zleHEMdqtAVnEbOjTDJA_fwt_HGNb"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EURO Gestión Cloud", layout="wide")

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""

# --- ACCESO ---
if not st.session_state['autenticado']:
    st.title("🏗️ Sistema EURO Control")
    t1, t2, t3 = st.tabs(["🔐 Login", "📝 Registro", "📧 Recuperar"])
    
    with t1:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR"):
                res = supabase.table("usuarios").select("*").eq("usuario", u).eq("clave", p).execute()
                if res.data:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = u
                    st.rerun()
                else:
                    st.error("Datos incorrectos")

    with t2:
        with st.form("reg"):
            nu = st.text_input("Nuevo Usuario")
            ne = st.text_input("Correo")
            np = st.text_input("Nueva Clave", type="password")
            if st.form_submit_button("REGISTRAR"):
                supabase.table("usuarios").insert({"usuario": nu, "correo": ne, "clave": np}).execute()
                st.success("Cuenta creada")

    with t3:
        em = st.text_input("Correo de recuperación")
        if st.button("Recuperar"):
            res = supabase.table("usuarios").select("*").eq("correo", em).execute()
            if res.data:
                st.info(f"Usuario: {res.data[0]['usuario']} | Clave: {res.data[0]['clave']}")

# --- APP PRINCIPAL ---
else:
    st.sidebar.title(f"👤 {st.session_state['usuario']}")
    opcion = st.sidebar.radio("Menú", ["Registrar", "Buscar", "Salir"])

    if opcion == "Salir":
        st.session_state['autenticado'] = False
        st.rerun()

    elif opcion == "Registrar":
        st.header("📝 Nuevo Reporte")
        with st.form("trabajo", clear_on_submit=True):
            area = st.text_input("📍 Área")
            equipo = st.text_input("📦 Equipo")
            desc = st.text_area("📝 Descripción")
            archivo = st.file_uploader("📷 Foto/Video", type=["jpg","png","jpeg","mp4"])
            
            if st.form_submit_button("GUARDAR"):
                if equipo and archivo:
                    fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{archivo.name}"
                    supabase.storage.from_("evidencias").upload(fname, archivo.getvalue())
                    url = supabase.storage.from_("evidencias").get_public_url(fname)
                    
                    datos = {
                        "fecha": datetime.now().strftime("%d/%m/%Y"),
                        "tecnico": st.session_state['usuario'],
                        "area": area,
                        "equipo": equipo,
                        "descripcion": desc,
                        "url_multimedia": url
                    }
                    supabase.table("reportes_euro").insert(datos).execute()
                    st.success("✅ Guardado")
                else:
                    st.error("Faltan datos")

    elif opcion == "Buscar":
        st.header("🔍 Historial")
        res = supabase.table("reportes_euro").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            for _, r in df.iloc[::-1].iterrows():
                with st.expander(f"{r['fecha']} - {r['equipo']}"):
                    st.write(f"**Técnico:** {r['tecnico']} | **Área:** {r['area']}")
                    st.write(f"**Descripción:** {r['descripcion']}")
                    if r['url_multimedia'].lower().endswith('.mp4'):
                        st.video(r['url_multimedia'])
                    else:
                        st.image(r['url_multimedia'])
