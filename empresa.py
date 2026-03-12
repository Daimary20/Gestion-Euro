

import streamlit as st
import pandas as pd
from datetime import datetime
import requests # Necesitaremos esta para enviar datos a Google

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EURO Gestión Cloud", layout="wide")
ADMIN_PASSWORD = "admin" # Cambia tu clave aquí

# URL de tu Google App Script (la obtendrás en el paso anterior)
GOOGLE_SCRIPT_URL = "AQUÍ_PEGARÁS_TU_LINK_DE_GOOGLE"

st.sidebar.title("🛠️ EURO Control")
opcion = st.sidebar.radio("Menú", ["📝 Reportar Trabajo", "📊 Panel de Control"])

if opcion == "📝 Reportar Trabajo":
    st.header("Nuevo Reporte de Actividad")
    with st.form("form_registro"):
        nombre = st.text_input("Técnico")
        equipo = st.text_input("Máquina/Equipo")
        desc = st.text_area("Descripción")
        foto = st.file_uploader("Subir Foto", type=["jpg", "png"])
        
        if st.form_submit_button("ENVIAR A LA NUBE"):
            if nombre and equipo and foto:
                # Aquí el código enviará los datos a Google Sheets
                st.success("✅ Reporte enviado y guardado en Google Sheets")
            else:
                st.error("Completa todos los campos")

else:
    # Lógica para ver el historial conectándose a la hoja de Google
    st.header("Panel Administrativo")
    pw = st.sidebar.text_input("Clave", type="password")
    if pw == ADMIN_PASSWORD:
        st.write("Conectando con la base de datos de Google...")
        # Aquí leeremos la hoja de cálculo directamente
