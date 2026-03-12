import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EURO Gestión Pro", layout="wide")

# CONFIGURACIÓN DE ENLACES (Pega los tuyos aquí)
URL_GOOGLE_SCRIPT = "https://gestion-euro-iebyhcq3f9vhb82ov7hhax.streamlit.app/~/+/LINK_DE_TU_HOJA_DE_CALCULO_AQUI#nuevo-reporte-de-actividad"
URL_CSV_LECTURA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTrL2GKdcGjFfPBsh-3nm-gshEqx_05OMloc3N1Q0s3yFQt8Qpq0uMTGvlb_2KwF0GGmPaVPOA3my_N/pub?output=csv"

st.sidebar.title("🛠️ Menú EURO")
opcion = st.sidebar.radio("Ir a:", ["📝 Nuevo Reporte", "📊 Ver Historial / Buscar"])

# --- SECCIÓN 1: GUARDAR EN GOOGLE SHEETS ---
if opcion == "📝 Nuevo Reporte":
    st.header("Registrar Nuevo Trabajo")
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        emp = col1.text_input("Técnico")
        area = col2.text_input("Área/Cliente")
        prod = st.text_input("Equipo/Máquina")
        desc = st.text_area("Descripción del trabajo")
        
        if st.form_submit_button("GUARDAR REPORTE"):
            if emp and prod and area:
                datos = {
                    "fecha": datetime.now().strftime("%d/%m/%Y"),
                    "hora": datetime.now().strftime("%H:%M"),
                    "empleado": emp,
                    "area": area,
                    "producto": prod,
                    "descripcion": desc,
                    "foto_url": "Almacenado"
                }
                # Envío a Google Sheets
                requests.post(URL_GOOGLE_SCRIPT, data=json.dumps(datos))
                st.success("✅ Guardado en Google Sheets correctamente.")
            else:
                st.error("Por favor llena los campos obligatorios.")

# --- SECCIÓN 2: VER REPORTES DESDE LA APP ---
else:
    st.header("📊 Historial Completo de Reportes")
    pw = st.sidebar.text_input("Contraseña Admin", type="password")
    
    if pw == "admin": # Puedes cambiar esta clave
        try:
            # La app lee los datos de Google Sheets
            df = pd.read_csv(URL_CSV_LECTURA)
            
            # Buscador avanzado
            busqueda = st.text_input("🔍 Buscar por cualquier palabra (Técnico, Área, Máquina...)")
            
            if busqueda:
                # Filtra en todas las columnas
                df = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]

            # Muestra la tabla profesional
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Resumen rápido
            st.info(f"Mostrando {len(df)} reportes encontrados.")
            
        except Exception as e:
            st.warning("Aún no hay datos para mostrar o el enlace de publicación no es correcto.")
    else:
        st.info("Introduce la contraseña en el menú lateral para ver los reportes.")



