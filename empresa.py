import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EURO Control Pro", layout="wide")

DB_FILE = "base_datos_trabajos.csv"
FOTOS_DIR = "fotos"

# Crear carpeta de fotos si no existe (para uso local)
if not os.path.exists(FOTOS_DIR):
    os.makedirs(FOTOS_DIR)

# --- MENÚ ---
st.sidebar.title("🛠️ Sistema EURO")
opcion = st.sidebar.radio("Navegación:", ["📝 Nuevo Reporte", "🔍 Buscador con Fotos"])

# --- OPCIÓN 1: NUEVO REPORTE ---
if opcion == "📝 Nuevo Reporte":
    st.header("📝 Registro de Actividad")
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        tecnico = col1.text_input("👤 Técnico")
        area = col2.text_input("📍 Área")
        producto = st.text_input("📦 Equipo")
        desc = st.text_area("📝 Descripción")
        foto = st.file_uploader("📷 Foto (OBLIGATORIA)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("REGISTRAR TRABAJO"):
            if tecnico and producto and foto is not None:
                # Guardar la imagen físicamente
                nombre_foto = f"{tecnico}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                ruta_foto = os.path.join(FOTOS_DIR, nombre_foto)
                img = Image.open(foto)
                img.save(ruta_foto)
                
                datos = {
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Hora": datetime.now().strftime("%H:%M"),
                    "Técnico": tecnico,
                    "Área": area,
                    "Producto": producto,
                    "Descripción": desc,
                    "Archivo_Foto": nombre_foto # Guardamos el nombre del archivo
                }
                
                df_nuevo = pd.DataFrame([datos])
                df_nuevo.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False, encoding='utf-8-sig')
                st.success("✅ Guardado con éxito y foto registrada.")
            else:
                st.error("⚠️ Debes llenar Técnico, Equipo y adjuntar la FOTO.")

# --- OPCIÓN 2: BUSCADOR CON FOTOS ---
else:
    st.header("🔍 Buscador de Reportes con Evidencia")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        busqueda = st.text_input("🔍 Buscar por técnico, área o equipo...")
        
        if busqueda:
            df = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        
        # MOSTRAR REPORTES CON IMAGEN
        for index, row in df.iterrows():
            with st.expander(f"📅 {row['Fecha']} - {row['Técnico']} - {row['Producto']}"):
                col_text, col_img = st.columns([2, 1])
                
                with col_text:
                    st.write(f"**📍 Área:** {row['Área']}")
                    st.write(f"**📝 Descripción:** {row['Descripción']}")
                    st.write(f"**🕒 Hora:** {row['Hora']}")
                
                with col_img:
                    path_img = os.path.join(FOTOS_DIR, row['Archivo_Foto'])
                    if os.path.exists(path_img):
                        st.image(path_img, caption="Evidencia del trabajo", use_container_width=True)
                    else:
                        st.warning("Foto no encontrada en el servidor.")
    else:
        st.info("No hay registros todavía.")
