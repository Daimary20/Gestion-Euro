import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- CONEXIÓN DETECTADA ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co" 
KEY_SUPABASE = "sb_publishable_h7zleHEMdqtAvnEbOjTDJA_fwt_HId_I0u9Xf9m9n0-Qy9V8g7rX-E_h-YJ_H0_jL"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

st.set_page_config(page_title="EURO Gestión Cloud", layout="wide")

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""

# --- LOGIN Y RECUPERACIÓN ---
if not st.session_state['autenticado']:
    st.title("🏗️ Sistema EURO Control")
    t1, t2, t3 = st.tabs(["🔐 Login", "📝 Registro", "📧 Recuperar"])
    
    with t1:
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("ENTRAR"):
                res = supabase.table("usuarios").select("*").eq("usuario", u).eq("clave", p).execute()
                if res.data:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = u
                    st.rerun()
                else: st.error("Datos incorrectos")

    with t2:
        with st.form("reg_form"):
            nu = st.text_input("Nuevo Usuario")
            ne = st.text_input("Correo para Recuperación")
            np = st.text_input("Contraseña", type="password")
            if st.form_submit_button("REGISTRARME"):
                try:
                    supabase.table("usuarios").insert({"usuario": nu, "correo": ne, "clave": np}).execute()
                    st.success("✅ Cuenta creada con éxito")
                except: st.error("Error: Asegúrate de correr el SQL en Supabase primero.")

    with t3:
        st.subheader("¿Olvidaste tus datos?")
        correo_rec = st.text_input("Introduce tu correo registrado")
        if st.button("VER MIS CREDENCIALES"):
            res = supabase.table("usuarios").select("*").eq("correo", correo_rec).execute()
            if res.data:
                st.info(f"👤 Usuario: {res.data[0]['usuario']} | 🔑 Clave: {res.data[0]['clave']}")
            else: st.error("Correo no encontrado.")

else:
    # --- PANEL PRINCIPAL ---
    st.sidebar.title(f"👤 {st.session_state['usuario']}")
    menu = st.sidebar.radio("Menú", ["Registrar Trabajo", "Historial", "Salir"])

    if menu == "Salir":
        st.session_state['autenticado'] = False
        st.rerun()

    elif menu == "Registrar Trabajo":
        with st.form("trabajo", clear_on_submit=True):
            ar, eq = st.columns(2)
            area = ar.text_input("📍 Área")
            equipo = eq.text_input("📦 Equipo")
            desc = st.text_area("📝 Descripción")
            f = st.file_uploader("📷 Foto o Video", type=["jpg","png","jpeg","mp4"])
            if st.form_submit_button("GUARDAR"):
                if equipo and f:
                    try:
                        fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{f.name}"
                        supabase.storage.from_("evidencias").upload(fname, f.getvalue())
                        url = supabase.storage.from_("evidencias").get_public_url(fname)
                        supabase.table("reportes_euro").insert({
                            "fecha": datetime.now().strftime("%d/%m/%Y"),
                            "tecnico": st.session_state['usuario'],
                            "area": area, "equipo": equipo, "descripcion": desc, "url_multimedia": url
                        }).execute()
                        st.success("✅ Guardado correctamente")
                    except: st.error("Error al subir. Revisa el Bucket 'evidencias'.")
                else: st.error("Faltan datos obligatorios")

    elif menu == "Historial":
        res = supabase.table("reportes_euro").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            for _, r in df.iloc[::-1].iterrows():
                with st.expander(f"📋 {r['fecha']} - {r['equipo']}"):
                    st.write(f"Técnico: {r['tecnico']} | Área: {r['area']}")
                    st.write(r['descripcion'])
                    if r['url_multimedia'].lower().endswith('.mp4'): st.video(r['url_multimedia'])
                    else: st.image(r['url_multimedia'])
