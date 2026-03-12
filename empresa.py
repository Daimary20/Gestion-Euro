import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONEXIÓN A SUPABASE ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co" 
# Esta es la 'Publishable key' que vi en tu captura image_01c2b9.png
KEY_SUPABASE = "sb_publishable_h7zleHEMdqtAvnEbOjTDJA_fwt_HId_I0u9Xf9m9n0-Qy9V8g7rX-E_h-YJ_H0_jL"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EURO Gestión Cloud", layout="wide")

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""

# --- PANTALLA DE ACCESO ---
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
                else:
                    st.error("Datos incorrectos")

    with t2:
        with st.form("reg_form"):
            nu = st.text_input("Nombre de Usuario")
            ne = st.text_input("Correo Electrónico")
            np = st.text_input("Contraseña Nueva", type="password")
            if st.form_submit_button("REGISTRARME"):
                try:
                    # Aquí se corrigió el error de la línea 37
                    supabase.table("usuarios").insert({"usuario": nu, "correo": ne, "clave": np}).execute()
                    st.success("✅ Cuenta creada. Ya puedes loguearte.")
                except Exception as e:
                    st.error(f"Error: Asegúrate de ejecutar el SQL en Supabase primero.")

    with t3:
        em = st.text_input("Correo registrado")
        if st.button("RECOBRAR DATOS"):
            res = supabase.table("usuarios").select("*").eq("correo", em).execute()
            if res.data:
                st.info(f"Usuario: {res.data[0]['usuario']} | Clave: {res.data[0]['clave']}")
            else:
                st.error("Correo no encontrado")

# --- APP PRINCIPAL ---
else:
    st.sidebar.title(f"👤 {st.session_state['usuario']}")
    opcion = st.sidebar.radio("Menú", ["Registrar Trabajo", "Historial", "Salir"])

    if opcion == "Salir":
        st.session_state['autenticado'] = False
        st.rerun()

    elif opcion == "Registrar Trabajo":
        with st.form("trabajo", clear_on_submit=True):
            ar = st.text_input("📍 Área")
            eq = st.text_input("📦 Equipo")
            de = st.text_area("📝 Descripción")
            f = st.file_uploader("📷 Foto/Video", type=["jpg","png","jpeg","mp4"])
            if st.form_submit_button("GUARDAR"):
                if eq and f:
                    try:
                        fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{f.name}"
                        supabase.storage.from_("evidencias").upload(fname, f.getvalue())
                        url = supabase.storage.from_("evidencias").get_public_url(fname)
                        
                        supabase.table("reportes_euro").insert({
                            "fecha": datetime.now().strftime("%d/%m/%Y"),
                            "tecnico": st.session_state['usuario'],
                            "area": ar, "equipo": eq, "descripcion": de, "url_multimedia": url
                        }).execute()
                        st.success("✅ Guardado en la nube")
                    except:
                        st.error("Error al subir. Revisa si el Bucket 'evidencias' es público.")
                else:
                    st.error("Faltan datos")

    elif opcion == "Historial":
        res = supabase.table("reportes_euro").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            for _, r in df.iloc[::-1].iterrows():
                with st.expander(f"📋 {r['fecha']} - {r['equipo']}"):
                    st.write(f"**Técnico:** {r['tecnico']} | **Área:** {r['area']}")
                    st.write(r['descripcion'])
                    if r['url_multimedia'].lower().endswith('.mp4'):
                        st.video(r['url_multimedia'])
                    else:
                        st.image(r['url_multimedia'])
