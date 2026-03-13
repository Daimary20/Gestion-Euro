import streamlit as st
from datetime import datetime
from supabase import create_client, Client
from fpdf import FPDF
import extra_streamlit_components as stx
import re

# --- 1. CONFIGURACIÓN ---
# He verificado la clave según tu error 401 para que no haya espacios extra
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3xG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"

# Código que deben conocer los técnicos para registrarse
CODIGO_REGISTRO_ADMIN = "EURO2026" 

if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(URL_SUPABASE, KEY_SUPABASE)

supabase = st.session_state.supabase

st.set_page_config(page_title="EURO Gestión Cloud", layout="wide", page_icon="🏗️")

# --- GESTIÓN DE SESIÓN PERSISTENTE (COOKIES) ---
# Se define fuera de funciones con caché para evitar el error de tu captura
cookie_manager = stx.CookieManager()

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# Intento de login automático
if not st.session_state['autenticado']:
    user_saved = cookie_manager.get(cookie="euro_user_session")
    if user_saved:
        st.session_state['autenticado'] = True
        st.session_state['usuario'] = user_saved

# --- FUNCIONES DE VALIDACIÓN Y PDF ---
def es_correo_valido(correo):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, correo) is not None

def generar_pdf(lista_reportes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "EURO GESTION - REPORTE DE TRABAJOS", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(30, 8, "Fecha", 1, 0, "L", True)
    pdf.cell(40, 8, "Equipo", 1, 0, "L", True)
    pdf.cell(40, 8, "Tecnico", 1, 0, "L", True)
    pdf.cell(80, 8, "Detalles", 1, 1, "L", True)
    pdf.set_font("Arial", "", 8)
    for r in lista_reportes:
        pdf.cell(30, 8, str(r.get('fecha', ''))[:10], 1)
        pdf.cell(40, 8, str(r.get('equipo', ''))[:20], 1)
        pdf.cell(40, 8, str(r.get('tecnico', ''))[:15], 1)
        pdf.cell(80, 8, str(r.get('descripcion', ''))[:50], 1, 1)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 2. ACCESO Y SEGURIDAD ---
if not st.session_state['autenticado']:
    st.title("🏗️ EURO Control")
    tab1, tab2, tab3 = st.tabs(["🔐 Entrar", "📝 Registro Técnico", "📧 Recuperar"])
    
    with tab1:
        u = st.text_input("Usuario o Cédula", key="u_login").strip()
        p = st.text_input("Clave", type="password", key="p_login").strip()
        recordar = st.checkbox("Recordarme en este dispositivo")
        
        if st.button("Iniciar Sesión"):
            try:
                # Login con Usuario o Cédula
                res = supabase.table("usuarios").select("*").or_(f"usuario.eq.{u},cedula.eq.{u}").eq("clave", p).execute()
                if res.data:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = res.data[0]['usuario']
                    if recordar:
                        cookie_manager.set("euro_user_session", res.data[0]['usuario'], key="set_cookie")
                    st.rerun()
                else:
                    st.error("Datos incorrectos. Revisa tu Cédula/Usuario y Clave.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

    with tab2:
        st.subheader("Nuevo Registro")
        nu = st.text_input("Nombre de Usuario", key="u_reg").strip()
        ci = st.text_input("Cédula de Identidad (Solo números)", key="c_reg").strip()
        ne = st.text_input("Correo Personal", key="e_reg").strip()
        np = st.text_input("Crear Contraseña (mín. 6 carac.)", type="password", key="p_reg").strip()
        codigo_auth = st.text_input("Código de Autorización de Empresa", type="password")
        
        if st.button("Completar Registro"):
            if not nu or not ci or not ne or not np:
                st.warning("Debe llenar todos los campos")
            elif not ci.isdigit():
                st.error("La Cédula debe contener solo números")
            elif not es_correo_valido(ne):
                st.error("El formato del correo electrónico no es válido")
            elif len(np) < 6:
                st.error("La contraseña debe tener al menos 6 caracteres")
            elif codigo_auth != CODIGO_REGISTRO_ADMIN:
                st.error("Código de Empresa incorrecto. Contacte a su supervisor.")
            else:
                try:
                    # Verificar si ya existe el usuario o la cédula
                    check = supabase.table("usuarios").select("*").or_(f"usuario.eq.{nu},cedula.eq.{ci}").execute()
                    if check.data:
                        st.error("El nombre de usuario o la cédula ya están registrados")
                    else:
                        supabase.table("usuarios").insert({
                            "usuario": nu, "cedula": ci, "correo": ne, "clave": np
                        }).execute()
                        st.success("✅ Registro exitoso. Ya puede iniciar sesión.")
                except Exception as e:
                    st.error(f"Error al registrar: {e}")

    with tab3:
        email_b = st.text_input("Correo registrado", key="e_rec")
        if st.button("Recuperar Datos"):
            try:
                res = supabase.table("usuarios").select("*").eq("correo", email_b).execute()
                if res.data:
                    st.info(f"Usuario: {res.data[0]['usuario']} | Cédula: {res.data[0]['cedula']} | Clave: {res.data[0]['clave']}")
                else:
                    st.warning("Correo no encontrado")
            except:
                st.error("Error en base de datos")

else:
    # --- 3. PANEL DE TRABAJO ---
    st.sidebar.title("EURO Control")
    st.sidebar.write(f"👤 Bienvenido: **{st.session_state['usuario']}**")
    
    if st.sidebar.button("🚪 Cerrar Sesión"):
        cookie_manager.delete("euro_user_session")
        st.session_state['autenticado'] = False
        st.rerun()

    menu = st.sidebar.radio("Menú Principal", ["➕ Registrar Trabajo", "📋 Historial"])

    if menu == "➕ Registrar Trabajo":
        st.header("📝 Registro de Actividad")
        f_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        with st.form("f_trabajo", clear_on_submit=True):
            eq = st.text_input("Equipo o Vehículo")
            ar = st.text_input("Área / Ubicación")
            de = st.text_area("Detalles de la labor realizada")
            f = st.file_uploader("Evidencia Multimedia", type=["jpg","png","jpeg","mp4","mov"])
            
            if st.form_submit_button("Guardar"):
                if eq and f:
                    try:
                        fname = f"{datetime.now().strftime('%Y%m%d%H%M')}_{f.name}"
                        supabase.storage.from_("evidencias").upload(fname, f.getvalue())
                        url = supabase.storage.from_("evidencias").get_public_url(fname)
                        supabase.table("reportes_euro").insert({
                            "fecha": f_actual, "tecnico": st.session_state['usuario'],
                            "area": ar, "equipo": eq, "descripcion": de, "url_multimedia": url
                        }).execute()
                        st.success("✅ Actividad guardada correctamente")
                    except Exception as e:
                        st.error(f"Error al subir: {e}")
                else:
                    st.warning("Debe ingresar el Equipo y subir una Evidencia")

    if menu == "📋 Historial":
        st.header("📋 Historial de Trabajos")
        busq = st.text_input("🔍 Buscar por Cédula, Técnico, Equipo o Fecha")
        try:
            res = supabase.table("reportes_euro").select("*").execute()
            if res.data:
                datos = res.data[::-1]
                if busq:
                    b = busq.lower()
                    datos = [r for r in datos if b in r['tecnico'].lower() or b in r['area'].lower() or b in (r['equipo'].lower() if r['equipo'] else "") or b in r['fecha'].lower()]
                
                if datos:
                    pdf_bytes = generar_pdf(datos)
                    st.download_button("📥 Exportar a PDF", data=pdf_bytes, file_name=f"reporte_{datetime.now().strftime('%d_%m')}.pdf", mime="application/pdf")

                for r in datos:
                    with st.expander(f"📅 {r['fecha']} | {r['equipo']}"):
                        st.write(f"👤 Técnico: {r['tecnico']} | 📍 Área: {r['area']}")
                        st.write(f"🛠️ Descripción: {r['descripcion']}")
                        if r['url_multimedia']:
