import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EURO Gestión Pro", layout="wide")

# Nombre del archivo donde se guarda TODO (Casillas + Fotos)
DB_FILE = "datos_euro.csv"

# Función para convertir la foto a texto y guardarla en el archivo
def procesar_foto(archivo_subido):
    img = Image.open(archivo_subido)
    img.thumbnail((600, 600)) # Reducimos tamaño para que sea ligero
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# --- MENÚ ---
st.sidebar.title("🛠️ Sistema EURO")
opcion = st.sidebar.radio("Navegación:", ["📝 Registrar Trabajo", "🔍 Buscador Avanzado"])

# --- 1. REGISTRO (Aquí se guarda lo de las casillas) ---
if opcion == "📝 Registrar Trabajo":
    st.header("📝 Nuevo Reporte de Actividad")
    
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        # CASILLAS DE INFORMACIÓN
        tecnico = col1.text_input("👤 Nombre del Técnico")
        area = col2.text_input("📍 Área / Ubicación")
        
        producto = st.text_input("📦 Equipo / Máquina")
        
        col3, col4 = st.columns(2)
        fec = col3.date_input("📅 Fecha", datetime.now())
        hor = col4.time_input("🕒 Hora", datetime.now())
        
        desc = st.text_area("📝 Descripción del trabajo realizado")
        
        # FOTO
        foto = st.file_uploader("📷 Adjuntar Foto (OBLIGATORIO)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("GUARDAR REPORTE"):
            if tecnico and producto and foto:
                # 1. Convertimos la foto a texto
                foto_texto = procesar_foto(foto)
                
                # 2. Creamos el diccionario con toda la información de las casillas
                datos = {
                    "Fecha": fec.strftime("%d/%m/%Y"),
                    "Hora": hor.strftime("%H:%M"),
                    "Técnico": tecnico,
                    "Área": area,
                    "Equipo": producto,
                    "Descripción": desc,
                    "Foto_Evidencia": foto_texto # La foto se guarda como texto aquí
                }
                
                # 3. Guardamos en el archivo CSV
                df_nuevo = pd.DataFrame([datos])
                df_nuevo.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False, encoding='utf-8-sig')
                
                st.success(f"✅ ¡Hecho! El reporte de {tecnico} se ha guardado con éxito.")
                st.balloons()
            else:
                st.error("⚠️ Error: Debes completar Técnico, Equipo y la Foto.")

# --- 2. BUSCADOR (Aquí se consulta lo guardado) ---
else:
    st.header("🔍 Buscador de Reportes")
    
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        
        # Filtro de búsqueda
        filtro = st.text_input("🔍 Buscar por cualquier dato (Nombre, Área, Fecha...)")
        
        if filtro:
            df = df[df.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)]
        
        # Mostrar los más recientes primero
        df = df.iloc[::-1]

        for _, row in df.iterrows():
            with st.expander(f"📋 {row['Fecha']} | {row['Técnico']} | {row['Equipo']}"):
                c1, c2 = st.columns([2, 1])
                
                with c1:
                    # Aquí se muestra la información de las casillas que guardamos
                    st.write(f"**🕒 Hora:** {row['Hora']}")
                    st.write(f"**📍 Área:** {row['Área']}")
                    st.write(f"**📝 Descripción:** {row['Descripción']}")
                
                with c2:
                    # Aquí mostramos la foto que guardamos
                    if 'Foto_Evidencia' in row and pd.notna(row['Foto_Evidencia']):
                        st.image(base64.b64decode(row['Foto_Evidencia']), use_container_width=True)
    else:
        st.info("No hay reportes registrados todavía.")
