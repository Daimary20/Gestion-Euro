import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="EURO Control", layout="wide")

# Nombre del archivo de base de datos local
DB_FILE = "base_datos_trabajos.csv"

# --- MENÚ LATERAL ---
st.sidebar.title("🛠️ Sistema EURO")
opcion = st.sidebar.radio("Ir a:", ["📝 Nuevo Reporte", "🔍 Buscador Avanzado"])

# --- OPCIÓN 1: FORMULARIO DE REPORTE ---
if opcion == "📝 Nuevo Reporte":
    st.header("📝 Registro de Actividad")
    
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        tecnico = col1.text_input("👤 Nombre del Técnico")
        area = col2.text_input("📍 Área / Ubicación del Trabajo")
        
        producto = st.text_input("📦 Equipo / Máquina Intervenida")
        
        col3, col4 = st.columns(2)
        fecha = col3.date_input("📅 Fecha", datetime.now())
        hora = col4.time_input("🕒 Hora", datetime.now())
        
        desc = st.text_area("📝 Descripción de la labor realizada")
        
        # FOTO OBLIGATORIA
        foto = st.file_uploader("📷 Adjuntar Fotografía del Trabajo (REQUERIDO)", type=["jpg", "png", "jpeg"])
        
        enviar = st.form_submit_button("REGISTRAR TRABAJO")
        
        if enviar:
            # Validación estricta: Técnico, Producto y Foto deben existir
            if tecnico and producto and foto is not None:
                datos = {
                    "Fecha": fecha.strftime("%d/%m/%Y"),
                    "Hora": hora.strftime("%H:%M"),
                    "Técnico": tecnico,
                    "Área": area,
                    "Producto": producto,
                    "Descripción": desc,
                    "Evidencia": "Foto Adjunta"
                }
                
                # Guardado en CSV
                df_nuevo = pd.DataFrame([datos])
                df_nuevo.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False, encoding='utf-8-sig')
                
                st.success(f"✅ ¡Excelente! Reporte de {tecnico} guardado correctamente.")
                st.balloons()
            else:
                if foto is None:
                    st.error("⚠️ NO SE PUEDE GUARDAR: Debes adjuntar obligatoriamente una imagen del trabajo.")
                else:
                    st.error("⚠️ Por favor, completa los campos de 'Técnico' y 'Equipo'.")

# --- OPCIÓN 2: BUSCADOR AVANZADO ---
else:
    st.header("🔍 Buscador Avanzado de Reportes")
    
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        
        # Campo de búsqueda global
        st.subheader("Filtrar información")
        busqueda = st.text_input("🔍 Busca por cualquier término (Ej: Nombre del técnico, una fecha, el área o el equipo)")
        
        # Filtro dinámico
        if busqueda:
            # Busca la coincidencia en todas las celdas de la tabla
            df_filtrado = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        else:
            df_filtrado = df

        # Mostrar tabla interactiva
        st.write(f"Mostrando **{len(df_filtrado)}** resultados encontrados.")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
        
        # Botón para exportar los resultados filtrados
        csv = df_filtrado.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Descargar esta lista en Excel (CSV)",
            data=csv,
            file_name=f"reporte_euro_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
        
    else:
        st.info("Aún no existen reportes registrados en la base de datos.")
        
