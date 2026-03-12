import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EURO Control Pro", layout="wide")

DB_FILE = "base_datos_trabajos.csv"
FOTOS_DIR = "fotos"

# Crear carpeta de fotos si no existe
if not os.path.exists(FOTOS_DIR):
    os.makedirs(FOTOS_DIR)

# --- MENÚ LATERAL ---
st.sidebar.title("🛠️ Sistema EURO")
opcion = st.sidebar.radio("Navegación:", ["📝 Nuevo Reporte", "🔍 Buscador Avanzado"])

# --- OPCIÓN 1: NUEVO REPORTE ---
if opcion == "📝 Nuevo Reporte":
    st.header("📝 Registro de Actividad")
    
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        tecnico = col1.text_input("👤 Técnico")
        area = col2.text_input("📍 Área / Ubicación")
        
        producto = st.text_input("📦 Equipo / Máquina")
        
        col3, col4 = st.columns(2)
        fec_manual = col3.date_input("📅 Fecha", datetime.now())
        hor_manual = col4.time_input("🕒 Hora", datetime.now())
        
        desc = st.text_area("📝 Descripción detallada")
        foto = st.file_uploader("📷 Foto (OBLIGATORIA)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("REGISTRAR TRABAJO"):
            if tecnico and producto and foto is not None:
                # Guardar imagen físicamente
                nombre_archivo_foto = f"{tecnico}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                ruta_foto = os.path.join(FOTOS_DIR, nombre_archivo_foto)
                img = Image.open(foto)
                img.save(ruta_foto)
                
                datos = {
                    "Fecha": fec_manual.strftime("%d/%m/%Y"),
                    "Hora": hor_manual.strftime("%H:%M"),
                    "Técnico": tecnico,
                    "Área": area,
                    "Producto": producto,
                    "Descripción": desc,
                    "Archivo_Foto": nombre_archivo_foto # Aquí se guarda el nombre
                }
                
                df_nuevo = pd.DataFrame([datos])
                df_nuevo.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False, encoding='utf-8-sig')
                st.success("✅ Reporte guardado con éxito.")
                st.balloons()
            else:
                st.error("⚠️ Falta información o la FOTO obligatoria.")

# --- OPCIÓN 2: BUSCADOR AVANZADO ---
else:
    st.header("🔍 Buscador de Reportes con Foto")
    
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        busqueda = st.text_input("🔍 Filtrar por Técnico, Área, Equipo o Fecha...")
        
        if busqueda:
            df = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        
        # Ordenar: Los más nuevos primero
        df = df.iloc[::-1]

        for index, row in df.iterrows():
            # El expander muestra un resumen
            with st.expander(f"📋 {row['Fecha']} | {row['Técnico']} | {row['Producto']}"):
                c1, c2 = st.columns([2, 1])
                
                with c1:
                    st.write(f"**🕒 Hora:** {row['Hora']}")
                    # Usamos .get por si la columna 'Área' o 'Area' cambia de nombre
                    st.write(f"**📍 Área:** {row.get('Área', row.get('Area', 'N/A'))}")
                    st.write(f"**📝 Descripción:** {row['Descripción']}")
                
                with c2:
                    # PROTECCIÓN CONTRA EL ERROR KEYERROR:
                    if 'Archivo_Foto' in row and pd.notna(row['Archivo_Foto']):
                        path_img = os.path.join(FOTOS_DIR, str(row['Archivo_Foto']))
                        if os.path.exists(path_img):
                            st.image(path_img, use_container_width=True)
                        else:
                            st.warning("Imagen no encontrada.")
                    else:
                        st.info("Este reporte no tiene foto.")
    else:
        st.info("No hay datos registrados aún.")
