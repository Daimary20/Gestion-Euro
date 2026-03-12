import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image
import hashlib

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EURO Gestión Pro", layout="wide")

DB_FILE = "datos_euro.csv"
USER_FILE = "usuarios_euro.csv"

# --- FUNCIONES DE SEGURIDAD ---
def filtrar_nombre(nombre):
    return hashlib.sha256(str.encode(nombre)).hexdigest()

def procesar_foto(archivo_subido):
    img = Image.open(archivo_subido)
    img.thumbnail((600, 600))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# --- GESTIÓN DE USUARIOS ---
if not os.path.exists(USER_FILE):
    # Usuario administrador inicial
    df_admin = pd.DataFrame([{"usuario": "admin", "clave": "1234", "rol": "admin"}])
    df_admin.to_csv(USER_FILE, index=False)

def validar_usuario(u, p):
    df_u = pd.read_csv(USER_FILE)
    df_u['clave'] = df_u['clave'].astype(str)
    user_match = df_u[(df_u['usuario'] == u) & (df_u['clave'] == p)]
    return not user_match.empty

# --- ESTADO DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""

# --- PANTALLA DE LOGIN ---
if not st.session_state['autenticado']:
    st.title("🔐 Acceso EURO Control")
    with st.form("login"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            if validar_usuario(u, p):
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = u
                st.rerun()
            else:
                st.error("Usuario o clave incorrectos")
else:
    # --- MENÚ PRINCIPAL (YA AUTENTICADO) ---
    st.sidebar.title(f"👤 {st.session_state['usuario']}")
    opciones = ["📝 Registrar Trabajo", "🔍 Buscador Avanzado"]
    
    # Solo el admin puede registrar nuevos técnicos
    if st.session_state['usuario'] == "admin":
        opciones.append("👥 Gestionar Técnicos")
    
    opciones.append("🚪 Cerrar Sesión")
    opcion = st.sidebar.radio("Menú:", opciones)

    if opcion == "🚪 Cerrar Sesión":
        st.session_state['autenticado'] = False
        st.rerun()

    # --- 1. REGISTRO DE TRABAJO ---
    elif opcion == "📝 Registrar Trabajo":
        st.header("📝 Nuevo Reporte de Actividad")
        with st.form("form_registro", clear_on_submit=True):
            # El nombre del técnico se toma automáticamente del usuario logueado
            st.info(f"Técnico Responsable: **{st.session_state['usuario']}**")
            
            area = st.text_input("📍 Área / Ubicación")
            producto = st.text_input("📦 Equipo / Máquina")
            
            col1, col2 = st.columns(2)
            fec = col1.date_input("📅 Fecha", datetime.now())
            hor = col2.time_input("🕒 Hora", datetime.now())
            
            desc = st.text_area("📝 Descripción del trabajo")
            foto = st.file_uploader("📷 Foto de Evidencia", type=["jpg", "png", "jpeg"])
            
            if st.form_submit_button("GUARDAR REPORTE"):
                if producto and foto:
                    foto_texto = procesar_foto(foto)
                    datos = {
                        "Fecha": fec.strftime("%d/%m/%Y"),
                        "Hora": hor.strftime("%H:%M"),
                        "Técnico": st.session_state['usuario'],
                        "Área": area,
                        "Equipo": producto,
                        "Descripción": desc,
                        "Foto_Evidencia": foto_texto
                    }
                    pd.DataFrame([datos]).to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False, encoding='utf-8-sig')
                    st.success("✅ Reporte guardado con éxito.")
                else:
                    st.error("⚠️ El equipo y la foto son obligatorios.")

    # --- 2. BUSCADOR ---
    elif opcion == "🔍 Buscador Avanzado":
        st.header("🔍 Buscador de Reportes")
        if os.path.exists(DB_FILE):
            df = pd.read_csv(DB_FILE)
            filtro = st.text_input("🔍 Buscar por Técnico, Área o Equipo...")
            if filtro:
                df = df[df.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)]
            
            for _, row in df.iloc[::-1].iterrows():
                with st.expander(f"📋 {row['Fecha']} | {row['Técnico']} | {row['Equipo']}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.write(f"**🕒 Hora:** {row['Hora']}")
                        st.write(f"**📍 Área:** {row['Área']}")
                        st.write(f"**📝 Descripción:** {row['Descripción']}")
                    with c2:
                        if 'Foto_Evidencia' in row and pd.notna(row['Foto_Evidencia']):
                            st.image(base64.b64decode(row['Foto_Evidencia']), use_container_width=True)
        else:
            st.info("No hay reportes.")

    # --- 3. GESTIÓN DE TÉCNICOS (SOLO ADMIN) ---
    elif opcion == "👥 Gestionar Técnicos":
        st.header("👥 Registro de Nuevos Técnicos")
        with st.form("nuevo_usuario"):
            nuevo_u = st.text_input("Nombre de Usuario (Técnico)")
            nueva_p = st.text_input("Clave", type="password")
            if st.form_submit_button("Crear Usuario"):
                if nuevo_u and nueva_p:
                    df_u = pd.read_csv(USER_FILE)
                    if nuevo_u in df_u['usuario'].values:
                        st.warning("El usuario ya existe.")
                    else:
                        nuevo_row = pd.DataFrame([{"usuario": nuevo_u, "clave": nueva_p, "rol": "user"}])
                        nuevo_row.to_csv(USER_FILE, mode='a', header=False, index=False)
                        st.success(f"Usuario {nuevo_u} creado correctamente.")
