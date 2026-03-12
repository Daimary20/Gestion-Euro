import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- CONEXIÓN ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co" 
KEY_SUPABASE = "TU_CLAVE_SB_PUBLISHABLE_AQUI" # Pon tu clave aquí
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

st.set_page_config(page_title="EURO Gestión Cloud", layout="wide")

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- LÓGICA DE ACCESO ---
if not st.session_state['autenticado']:
    st.title("🏗️ EURO Control")
    t1, t2, t3 = st.tabs(["🔐 Login", "📝 Registro", "📧 Recuperar"])
    
    with t1:
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            res = supabase.table("usuarios").select("*").eq("usuario", u).eq("clave", p).execute()
            if res.data:
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = u
                st.rerun()
            else: st.error("Error de acceso")

    with t2:
        nu = st.text_input("Nuevo Usuario")
        ne = st.text_input("Correo")
        np = st.text_input("Nueva Clave", type="password")
        if st.button("Registrar"):
            supabase.table("usuarios").insert({"usuario": nu, "correo": ne, "clave": np}).execute()
            st.success("¡Registrado!")

    with t3:
        em = st.text_input("Tu Correo")
        if st.button("Recuperar"):
            res = supabase.table("usuarios").select("*").eq("correo", em).execute()
            if res.data:
                st.info(f"Usuario: {res.data[0]['usuario']} | Clave: {res.data[0]['clave']}")
            else: st.error("Correo no encontrado")

else:
    # --- APP PRINCIPAL ---
    st.sidebar.write(f"Usuario: {st.session_state['usuario']}")
    if st.sidebar.button("Salir"):
        st.session_state['autenticado'] = False
        st.rerun()

    menu = st.sidebar.radio("Ir a:", ["Registrar", "Historial"])

    if menu == "Registrar":
        with st.form("registro"):
            eq = st.text_input("Equipo")
            ar = st.text_input("Área")
            de = st.text_area("Descripción")
            f = st.file_uploader("Foto/Video", type=["jpg","png","mp4"])
            if st.form_submit_button("Guardar"):
                if eq and f:
                    fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{f.name}"
                    supabase.storage.from_("evidencias").upload(fname, f.getvalue())
                    url = supabase.storage.from_("evidencias").get_public_url(fname)
                    
                    supabase.table("reportes_euro").insert({
                        "fecha": datetime.now().strftime("%d/%m/%Y"),
                        "tecnico": st.session_state['usuario'],
                        "area": ar, "equipo": eq, "descripcion": de, "url_multimedia": url
                    }).execute()
                    st.success("Guardado")
                else: st.error("Faltan datos")

    if menu == "Historial":
        res = supabase.table("reportes_euro").select("*").execute()
        for r in res.data[::-1]:
            with st.expander(f"{r['fecha']} - {r['equipo']}"):
                st.write(f"Técnico: {r['tecnico']} | Área: {r['area']}")
                st.write(de)
                if r['url_multimedia'].endswith('.mp4'): st.video(r['url_multimedia'])
                else: st.image(r['url_multimedia'])
