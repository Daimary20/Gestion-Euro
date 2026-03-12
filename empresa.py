import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EURO Gestión Pro", layout="wide")

# Nombre del archivo de datos interno
DB_FILE = "datos_internos_euro.csv"

# Función para procesar la imagen y convertirla en texto
def procesar_foto(archivo_subido):
    img = Image.open(archivo_subido)
    # Reducimos un poco el tamaño para que la app cargue rápido
    img.thumbnail((600, 600))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# --- MENÚ ---
st.sidebar.title("🛠️ Sistema EURO")
opcion = st.sidebar.radio("Navegación:", ["📝 Registrar Trabajo", "🔍 Buscador Avanzado"])

# --- 1. REGISTRO DE TRABAJO ---
if opcion == "📝 Registrar Trabajo":
    st.header("📝 Nuevo Reporte de Actividad")
    
    with st.form("form_euro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        tecnico = col1.text_input("👤 Nombre del Técnico")
        area = col2.text_input("📍 Área / Ubicación")
        
        producto = st.text_input("📦 Equipo / Máquina")
        
        col3, col4 = st.columns(2)
        fec = col3.date_input("📅 Fecha", datetime.now())
        hor = col4.time_input("🕒 Hora", datetime.now())
        
        desc = st.text_area("📝 Descripción detallada del trabajo")
        
        # FOTO OBLIGATORIA
        foto = st.file_uploader("📷 Adjuntar Foto de Evidencia (OBLIGATORIO)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("REGISTRAR EN EL SISTEMA"):
            if tecnico and producto and foto:
                # Convertimos la foto a texto para guardarla internamente
                foto_texto = procesar_foto(foto)
                
                datos = {
                    "Fecha": fec.strftime("%d/%m/%Y"),
                    "Hora": hor.strftime("%H:%M"),
                    "Técnico": tecnico,
                    "Área": area,
                    "Producto": producto,
                    "Descripción": desc,
                    "Imagen_Base64": foto_texto
                }
                
                # Guardado persistente
                df_nuevo = pd.DataFrame([datos])
                df_nuevo.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False, encoding='utf-8-sig')
                
                st.success(f"✅ Reporte de {tecnico} guardado correctamente.")
                st.balloons()
            else:
                st.error("⚠️ Error: El técnico, el equipo y la foto son obligatorios.")

# --- 2. BUSCADOR AVANZADO ---
else:
    st.header("🔍 Buscador de Reportes con Evidencia")
    
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        
        # Buscador dinámico
        filtro = st.text_input("🔍 Escribe para filtrar (Técnico, Área, Equipo o Fecha)...")
        
        if filtro:
            df = df[df.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)]
        
        # Mostramos los reportes más nuevos primero
        df = df.iloc[::-1]

        for _, row in df.iterrows():
            # Cada reporte es una "tarjeta" desplegable
            with st.expander(f"📋 {row['Fecha']} | {row['Técnico']} | {row['Producto']}"):
                c1, c2 = st.columns([2, 1])
                
                with c1:
                    st.write(f"**🕒 Hora:** {row['Hora']}")
                    st.write(f"**📍 Área:** {row['Área']}")
                    st.write(f"**📝 Descripción:** {row['Descripción']}")
                
                with c2:
                    # Mostrar la foto guardada
                    if 'Imagen_Base64' in row and pd.notna(row['Imagen_Base64']):
                        try:
                            st.image(base64.b64decode(row['Imagen_Base64']), use_container_width=True)
                        except:
                            st.warning("No se pudo cargar la imagen.")
                    else:
                        st.info("Sin foto registrada.")
    else:
        st.info("No hay reportes en la base de datos.")
