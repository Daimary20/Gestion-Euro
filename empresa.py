import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EURO Gestión Pro", layout="wide")

URL_GOOGLE_SCRIPT = "TU_URL_DE_APPS_SCRIPT_AQUI"
# AQUÍ PEGA EL LINK DE "PUBLICAR EN LA WEB" COMO CSV
URL_CSV_LECTURA = "TU_LINK_DE_PUBLICAR_EN_LA_WEB_CSV_AQUI"

st.sidebar.title("🛠️ Menú EURO")
opcion = st.sidebar.radio("Ir a:", ["📝 Reporte Diario", "📊 Panel Admin"])

# --- PESTAÑA 1: REPORTE (Se queda igual) ---
if opcion == "📝 Reporte Diario":
    st.header("Nuevo Reporte de Actividad")
    with st.form("form_euro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        emp = col1.text_input("👤 Nombre del Técnico")
        area = col2.text_input("📍 Área de Trabajo")
        prod = st.text_input("📦 Equipo / Máquina")
        
        col3, col4 = st.columns(2)
        fec = col3.date_input("📅 Fecha", datetime.now())
        hor = col4.time_input("🕒 Hora", datetime.now())
        
        desc = st.text_area("📝 Detalles del Trabajo")
        foto = st.file_uploader("📷 Foto", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("ENVIAR REPORTE"):
            datos = {
                "fecha": fec.strftime("%d/%m/%Y"),
                "hora": hor.strftime("%H:%M"),
                "empleado": emp,
                "area": area,
                "producto": prod,
                "descripcion": desc,
                "foto_url": "Ver en Drive"
            }
            requests.post(URL_GOOGLE_SCRIPT, data=json.dumps(datos))
            st.success("✅ Reporte guardado en la nube")

# --- PESTAÑA 2: PANEL ADMIN CON BUSCADOR ---
else:
    st.header("📊 Buscador de Reportes")
    pw = st.sidebar.text_input("Clave de Acceso", type="password")
    
    if pw == "admin": # Tu clave
        try:
            # Leemos los datos directamente de Google
            df = pd.read_csv(URL_CSV_LECTURA)
            
            # --- SECCIÓN DE FILTROS ---
            st.subheader("🔍 Filtros de Búsqueda")
            c1, c2, c3 = st.columns(3)
            
            busqueda_general = c1.text_input("Buscar por Técnico o Equipo")
            filtro_area = c2.selectbox("Filtrar por Área", ["Todas"] + list(df['Área'].unique()))
            filtro_fecha = c3.text_input("Buscar Fecha (DD/MM/YYYY)")

            # Aplicar filtros
            df_filtrado = df.copy()
            
            if busqueda_general:
                df_filtrado = df_filtrado[df_filtrado.astype(str).apply(lambda x: x.str.contains(busqueda_general, case=False)).any(axis=1)]
            
            if filtro_area != "Todas":
                df_filtrado = df_filtrado[df_filtrado['Área'] == filtro_area]
                
            if filtro_fecha:
                df_filtrado = df_filtrado[df_filtrado['Fecha'] == filtro_fecha]

            # --- MOSTRAR RESULTADOS ---
            st.write(f"Se encontraron **{len(df_filtrado)}** reportes.")
            
            # Tabla interactiva profesional
            st.dataframe(df_filtrado, use_container_width=True)
            
            # Botón para descargar lo que filtraste
            csv = df_filtrado.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Descargar esta búsqueda en Excel", csv, "busqueda_euro.csv", "text/csv")

        except:
            st.warning("Aún no hay datos en la nube o el link de lectura no es correcto.")
    else:
        st.error("Introduce la clave para ver el historial.")
