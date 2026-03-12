import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# --- CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(page_title="EURO Gestión Pro", layout="wide")

# --- REEMPLAZA CON TU URL DE GOOGLE APPS SCRIPT ---
URL_GOOGLE = "TU_URL_DE_APPS_SCRIPT_AQUI"

st.sidebar.title("🛠️ Menú EURO")
opcion = st.sidebar.radio("Ir a:", ["📝 Reporte Diario", "📊 Panel Admin"])

if opcion == "📝 Reporte Diario":
    st.header("Nuevo Reporte de Actividad")
    
    with st.form("form_euro", clear_on_submit=True):
        # Campos de identificación
        col_tecnico, col_area = st.columns(2)
        emp = col_tecnico.text_input("👤 Nombre del Técnico")
        area = col_area.text_input("📍 Área de Trabajo (Ej: Cocina, Taller, Cliente X)")
        
        # Campo de equipo
        prod = st.text_input("📦 Equipo / Máquina (Ej: Horno Blodgett)")
        
        # Campos de tiempo (Ahora editables)
        col_fecha, col_hora = st.columns(2)
        fec_manual = col_fecha.date_input("📅 Fecha del Trabajo", datetime.now())
        hor_manual = col_hora.time_input("🕒 Hora del Trabajo", datetime.now())
        
        # Descripción y Foto
        desc = st.text_area("📝 Detalles del Trabajo Realizado")
        foto = st.file_uploader("📷 Subir Foto del Trabajo", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("ENVIAR REPORTE A LA NUBE"):
            if emp and prod and area:
                # Preparamos los datos para Google Sheets
                datos = {
                    "fecha": fec_manual.strftime("%d/%m/%Y"),
                    "hora": hor_manual.strftime("%H:%M"),
                    "empleado": emp,
                    "area": area, # Enviamos la nueva variable Area
                    "producto": prod,
                    "descripcion": desc,
                    "foto_url": "Foto cargada" # Luego configuraremos la subida real de imagen
                }
                
                try:
                    requests.post(URL_GOOGLE, data=json.dumps(datos))
                    st.success(f"✅ ¡Excelente! El reporte de {prod} en {area} ha sido guardado.")
                    st.balloons()
                except:
                    st.error("❌ Error de conexión. Revisa el link de Google Script.")
            else:
                st.warning("⚠️ Por favor llena Nombre, Área y Producto.")

elif opcion == "📊 Panel Admin":
    st.header("Panel Administrativo")
    st.info("Desde aquí puedes acceder a tu base de datos central en Google.")
    # Coloca aquí el link de tu hoja de Google Sheets
    st.link_button("📂 Abrir Base de Datos (Excel)", "LINK_DE_TU_HOJA_DE_CALCULO_AQUI")
