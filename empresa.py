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
            foto = st.file_uploader("📷 Foto de Evidencia (Obligatoria)", type=["jpg", "png", "jpeg"])
            
            if st.form_submit_button("GUARDAR REPORTE"):
                if equipo and foto:
                    foto_txt = procesar_foto(foto)
                    datos = {
                        "Fecha": fec.strftime("%d/%m/%Y"),
                        "Hora": hor.strftime("%H:%M"),
                        "Técnico": st.session_state['usuario'],
                        "Área": area,
                        "Equipo": equipo,
                        "Descripción": desc,
                        "Foto_Data": foto_txt
                    }
                    pd.DataFrame([datos]).to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False, encoding='utf-8-sig')
                    st.success("✅ Reporte guardado.")
                    st.balloons()
                else:
                    st.error("⚠️ Faltan datos o la foto.")

    elif opcion == "🔍 Buscador Avanzado":
        st.header("🔍 Historial de Reportes")
        if os.path.exists(DB_FILE):
            df = pd.read_csv(DB_FILE)
            filtro = st.text_input("🔍 Buscar por área, equipo, técnico...")
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
                        if 'Foto_Data' in row and pd.notna(row['Foto_Data']):
                            st.image(base64.b64decode(row['Foto_Data']), use_container_width=True)
        else:
            st.info("No hay reportes todavía.")
