import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="EURO Gestión Pro", layout="wide")

DB_FILE = "datos_euro.csv"
USER_FILE = "usuarios_euro.csv"

# --- FUNCIONES TÉCNICAS ---
def procesar_foto(archivo_subido):
    img = Image.open(archivo_subido)
    img.thumbnail((600, 600))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def inicializar_usuarios():
    if not os.path.exists(USER_FILE):
        # Creamos el archivo con un admin por defecto
        df = pd.DataFrame([{"usuario": "admin", "clave": "1234"}])
        df.to_csv(USER_FILE, index=False)

def validar_login(u, p):
    df = pd.read_csv(USER_FILE)
    df['clave'] = df['clave'].astype(str)
    match = df[(df['usuario'] == u) & (df['clave'] == p)]
    return not match.empty

def registrar_usuario(u, p):
    df = pd.read_csv(USER_FILE)
    if u in df['usuario'].values:
        return False
    nuevo = pd.DataFrame([{"usuario": u, "clave": p}])
    nuevo.to_csv(USER_FILE, mode='a', header=False, index=False)
    return True

# --- INICIO DE LA APP ---
inicializar_usuarios()

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""

# --- PANTALLA DE ENTRADA (LOGIN / REGISTRO) ---
if not st.session_state['autenticado']:
    st.title("🏗️ Bienvenid@ a EURO Control")
    
    tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrar Nuevo Usuario"])
    
    with tab1:
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("ENTRAR"):
                if validar_login(u, p):
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = u
                    st.rerun()
                else:
                    st.error("Usuario o clave incorrectos")

    with tab2:
        st.subheader("Crea tu cuenta de técnico")
        with st.form("register_form"):
            new_u = st.text_input("Elige un nombre de Usuario")
            new_p = st.text_input("Crea una Contraseña", type="password")
            confirm_p = st.text_input("Confirma la Contraseña", type="password")
            
            if st.form_submit_button("REGISTRARME"):
                if new_u and new_p:
                    if new_p == confirm_p:
                        if registrar_usuario(new_u, new_p):
                            st.success("✅ Registro exitoso. Ya puedes iniciar sesión.")
                        else:
                            st.error("❌ El nombre de usuario ya existe.")
                    else:
                        st.warning("⚠️ Las contraseñas no coinciden.")
                else:
                    st.error("⚠️ Rellena todos los campos.")

# --- PANEL PRINCIPAL (YA DENTRO) ---
else:
    st.sidebar.title(f"👤 Técnico: {st.session_state['usuario']}")
    opcion = st.sidebar.radio("Navegación:", ["📝 Registrar Trabajo", "🔍 Buscador Avanzado", "🚪 Cerrar Sesión"])

    if opcion == "🚪 Cerrar Sesión":
        st.session_state['autenticado'] = False
        st.rerun()

    elif opcion == "📝 Registrar Trabajo":
        st.header("📝 Nuevo Reporte de Actividad")
        st.info(f"Registrando como: **{st.session_state['usuario']}**")
        
        with st.form("registro_trabajo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            area = col1.text_input("📍 Área / Ubicación")
            equipo = col2.text_input("📦 Equipo / Máquina")
            
            c3, c4 = st.columns(2)
            fec = c3.date_input("📅 Fecha", datetime.now())
            hor = c4.time_input("🕒 Hora", datetime.now())
            
            desc = st.text_area("📝 Descripción del trabajo")
            foto = st.file_uploader("📷 Foto de Evidencia (
