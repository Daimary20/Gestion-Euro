import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="EURO Control Pro", layout="wide")

DB_FILE = "base_datos_trabajos.csv"
FOTOS_DIR = "fotos"

# Crear carpeta de fotos si no existe
if not os.path.exists(FOTOS_DIR):
    os.makedirs(FOTOS_DIR)

# --- MENÚ LATERAL ---
st.sidebar.title("🛠️ Sistema EURO")
opcion = st.sidebar.radio("Navegación:", ["📝 Nuevo Reporte", "🔍 Buscador Avanzado"])

# --- OPCIÓN 1: NUEVO REPORTE (CON FECHA Y HORA MANUAL) ---
if opcion == "📝 Nuevo Reporte":
    st.header("📝 Registro de Actividad")
    
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        tecnico = col1.text_input("👤 Técnico")
        area = col2.text_input("📍 Área / Ubicación")
        
        producto = st.text_input("📦 Equipo / Máquina")
        
        # CAMPOS DE FECHA Y HORA QUE SOLICITASTE
        col3, col4 = st.columns(2)
        fec_manual = col3.date_input("📅 Fecha del Trabajo", datetime.now())
        hor_manual = col4.time_input("🕒 Hora del Trabajo", datetime.now())
        
        desc = st.text_area("📝 Descripción detallada")
        foto = st.file_uploader("📷 Foto de Evidencia (OBLIGATORIA)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("REGISTRAR TRABAJO"):
            if tecnico and producto and foto is not None:
                # Guardar imagen con nombre único
                nombre_foto = f"{tecnico}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                ruta_foto = os.path.join(FOTOS_DIR, nombre_foto)
                img = Image.open(foto)
                img.save(ruta_foto)
                
                datos = {
                    "Fecha": fec_manual.strftime("%d/%m/%Y"),
                    "Hora": hor_manual.strftime("%H:%M"),
                    "Técnico": tecnico,
                    "Área": area,
                    "Producto": producto,
                    "Descripción": desc,
                    "Archivo_Foto": nombre_foto
                }
                
                # Guardar en base de datos
                df_nuevo = pd.DataFrame([datos])
                df_nuevo.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False, encoding='utf-8-sig')
                st.success("✅ Reporte y foto guardados correctamente.")
            else:
                st.error("⚠️ Error: Debes completar Técnico, Equipo y adjuntar la FOTO.")

# --- OPCIÓN 2: BUSCADOR AVANZADO CON VISUALIZACIÓN ---
else:
    st.header("🔍 Buscador con Evidencia Fotográfica")
    
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        
        # Buscador general
        busqueda = st.text_input("🔍 Escribe técnico, área, equipo o fecha para filtrar...")
        
        if busqueda:
            df = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        
        # Invertir el orden para ver los más nuevos primero
        df = df.iloc[::-1]

        # Mostrar cada reporte de forma visual
        for index, row in df.iterrows():
            # Creamos una "tarjeta" por cada reporte
            with st.expander(f"📋 {row['Fecha']} | {row['Técnico']} | {row['Producto']}"):
                col_info, col_img = st.columns([2, 1])
                
                with col_info:
                    st.write(f"**🕒 Hora:** {row['Hora']}")
                    st.write(f"**📍 Área:** {row['Area'] if 'Area' in row else row['Área']}")
                    st.write(f"**📝 Descripción:** {row['Descripción']}")
                
                with col_img:
                    path_img = os.path.join(FOTOS_DIR, str(row['Archivo_Foto']))
                    if os.path.exists(path_img):
                        st.image(path_img, caption="Evidencia", use_container_width=True)
                    else:
                        st.warning("Foto no disponible para este registro.")
                        
        # Botón de descarga para el jefe
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Descargar base de datos (Excel/CSV)", csv, "reportes_euro.csv", "text/csv")
    else:
        st.info("No hay registros en la base de datos.")
