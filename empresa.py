import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EURO Control", layout="wide")

# Archivo donde se guardan los datos
DB_FILE = "base_datos_trabajos.csv"

# --- MENÚ LATERAL ---
st.sidebar.title("🛠️ Sistema EURO")
opcion = st.sidebar.radio("Selecciona una opción:", ["📝 Nuevo Reporte", "📊 Historial y Buscador"])

# --- OPCIÓN 1: NUEVO REPORTE ---
if opcion == "📝 Nuevo Reporte":
    st.header("📝 Registro de Trabajo")
    
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        tecnico = col1.text_input("👤 Técnico")
        area = col2.text_input("📍 Área / Ubicación")
        
        producto = st.text_input("📦 Equipo / Máquina")
        
        col3, col4 = st.columns(2)
        fecha = col3.date_input("📅 Fecha", datetime.now())
        hora = col4.time_input("🕒 Hora", datetime.now())
        
        desc = st.text_area("📝 Descripción detallada")
        
        enviar = st.form_submit_button("GUARDAR REPORTE")
        
        if enviar:
            if tecnico and producto:
                datos = {
                    "Fecha": fecha.strftime("%d/%m/%Y"),
                    "Hora": hora.strftime("%H:%M"),
                    "Técnico": tecnico,
                    "Área": area,
                    "Producto": producto,
                    "Descripción": desc
                }
                # Guardar en el archivo CSV local
                df_nuevo = pd.DataFrame([datos])
                df_nuevo.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False, encoding='utf-8-sig')
                st.success("✅ Reporte guardado con éxito.")
                st.balloons()
            else:
                st.error("⚠️ El nombre del Técnico y el Producto son obligatorios.")

# --- OPCIÓN 2: HISTORIAL Y BUSCADOR ---
else:
    st.header("📊 Consulta de Historial")
    
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        
        # Filtros de búsqueda (Sin contraseña)
        st.subheader("🔍 Buscador Inteligente")
        busqueda = st.text_input("Escribe para buscar (Técnico, Área, Equipo o Fecha)...")
        
        # Lógica de filtrado en tiempo real
        if busqueda:
            # Busca la palabra en cualquier columna de la tabla
            df = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        
        # Mostrar los resultados
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Botón para descargar en Excel
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Descargar Reporte (CSV)", csv, "reportes_euro.csv", "text/csv")
        
    else:
        st.info("Aún no hay reportes registrados.")
