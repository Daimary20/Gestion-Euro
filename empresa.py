import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EURO - Gestión Segura", layout="wide", page_icon="🔐")

# --- SEGURIDAD (Cambia tu contraseña aquí) ---
ADMIN_PASSWORD = "admin" # <-- PUEDES CAMBIAR ESTA CLAVE

# CSS para mejorar la estética
st.markdown("""
    <style>
    .report-card { 
        background-color: #ffffff; padding: 20px; border-radius: 12px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px;
        border-left: 5px solid #d32f2f; color: #333;
    }
    .stButton>button { border-radius: 10px; background-color: #d32f2f; color: white; }
    </style>
    """, unsafe_allow_html=True)

# Carpetas y archivos
if not os.path.exists("fotos_reportes"): os.makedirs("fotos_reportes")
DB_FILE = "base_datos_trabajos.csv"

def guardar_datos(fecha, hora, empleado, producto, descripcion, nombre_foto):
    nuevo_registro = pd.DataFrame([[fecha, hora, empleado, producto, descripcion, nombre_foto]], 
                                  columns=["Fecha", "Hora", "Empleado", "Producto", "Descripción", "Archivo_Foto"])
    nuevo_registro.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False, encoding='utf-8-sig')

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("🔐 Acceso EURO")
opcion = st.sidebar.radio("Ir a:", ["📝 Nuevo Reporte", "📊 Panel de Control"])

# --- PESTAÑA 1: REPORTE (PÚBLICA) ---
if opcion == "📝 Nuevo Reporte":
    st.title("🛠️ Registro de Trabajo")
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nombre = col1.text_input("👤 Tu Nombre")
        prod = col2.text_input("📦 Máquina / Producto")
        desc = st.text_area("📝 ¿Qué trabajo realizaste?")
        
        f_col, h_col = st.columns(2)
        fec = f_col.date_input("Fecha", datetime.now())
        hor = h_col.time_input("Hora", datetime.now())
        
        foto = st.file_uploader("📷 Subir Foto del Trabajo", type=["jpg", "png", "jpeg"])
        enviar = st.form_submit_button("GUARDAR REPORTE")

        if enviar:
            if nombre and prod and foto:
                fname = f"{fec}_{nombre}_{foto.name}".replace(" ", "_")
                with open(os.path.join("fotos_reportes", fname), "wb") as f:
                    f.write(foto.getbuffer())
                guardar_datos(fec, hor, nombre, prod, desc, fname)
                st.success("✅ Reporte guardado. ¡Buen trabajo!")
            else:
                st.error("⚠️ Falta completar datos o la foto.")

# --- PESTAÑA 2: PANEL DE CONTROL (RESTRINGIDA) ---
else:
    st.title("📊 Panel de Administración")
    password_input = st.sidebar.text_input("Introduce la contraseña de Admin", type="password")

    if password_input == ADMIN_PASSWORD:
        st.success("Acceso concedido")
        if os.path.exists(DB_FILE):
            df = pd.read_csv(DB_FILE)
            
            # Buscador y descarga
            busq = st.text_input("🔍 Buscar por empleado o producto")
            if busq:
                df = df[df['Producto'].str.contains(busq, case=False) | df['Empleado'].str.contains(busq, case=False)]
            
            st.download_button("📥 Descargar Excel", df.to_csv(index=False).encode('utf-8-sig'), "reporte_admin.csv")

            # Mostrar reportes
            for _, fila in df.sort_index(ascending=False).iterrows():
                st.markdown(f"""<div class="report-card">
                    <b>{fila['Fecha']}</b> - {fila['Producto']}<br>
                    <i>Realizado por: {fila['Empleado']}</i><br>
                    Descripción: {fila['Descripción']}
                </div>""", unsafe_allow_html=True)
                
                ruta = os.path.join("fotos_reportes", fila['Archivo_Foto'])
                if os.path.exists(ruta):
                    st.image(ruta, width=350)
        else:
            st.info("No hay datos registrados aún.")
    elif password_input == "":
        st.warning("Escribe la contraseña en la barra lateral para ver el historial.")
    else:
        st.error("❌ Contraseña incorrecta.")