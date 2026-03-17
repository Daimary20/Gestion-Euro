import streamlit as st
from datetime import datetime
from supabase import create_client, Client
from fpdf import FPDF
import extra_streamlit_components as stx

# --- CONFIGURACIÓN ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3eG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"
CODIGO_REGISTRO_ADMIN = "EURO2026" 
CODIGO_REGISTRO_JEFES = "ADMIN777" # Nuevo código para Jefes

if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(URL_SUPABASE, KEY_SUPABASE)

supabase = st.session_state.supabase
st.set_page_config(page_title="Euro Control Ingenieria", layout="wide", page_icon="🏗️")

# --- GESTIÓN DE SESIÓN ---
cookie_manager = stx.CookieManager()

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    try:
        user_saved = cookie_manager.get(cookie="euro_user_session")
        if user_saved:
            res_u = supabase.table("usuarios").select("*").eq("usuario", user_saved).execute()
            if res_u.data:
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = user_saved
                st.session_state['cargo_user'] = res_u.data[0].get('cargo', 'Técnico')
    except: pass

# --- FUNCIÓN PDF MEJORADA ---
def generar_pdf(lista_reportes):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(280, 10, "REPORTE DE GESTIÓN DETALLADO - EURO CONTROL INGENIERIA", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(240, 240, 240)
    headers = [("Fecha", 25), ("Equipo", 40), ("Área", 35), ("Responsable", 45), ("Descripción", 85), ("Seguimiento", 50)]
    for h, w in headers:
        pdf.cell(w, 8, h, 1, 0, "C", True)
    pdf.ln()

    pdf.set_font("Arial", "", 8)
    for r in lista_reportes:
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        pdf.multi_cell(25, 8, str(r.get('fecha', ''))[:10], 1, "C")
        pdf.set_xy(x_start + 25, y_start)
        pdf.multi_cell(40, 8, str(r.get('equipo', ''))[:40], 1, "L")
        pdf.set_xy(x_start + 65, y_start)
        pdf.multi_cell(35, 8, str(r.get('area', ''))[:30], 1, "L")
        pdf.set_xy(x_start + 100, y_start)
        pdf.multi_cell(45, 8, str(r.get('tecnico', ''))[:35], 1, "L")
        pdf.set_xy(x_start + 145, y_start)
        desc = str(r.get('descripcion', '')).replace('\n', ' ')
        pdf.multi_cell(85, 8, desc[:120], 1, "L")
        pdf.set_xy(x_start + 230, y_start)
        firma = r.get('comentario_supervisor', 'Pendiente')
        pdf.multi_cell(50, 8, str(firma)[:50], 1, "L")
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- INTERFAZ DE ACCESO ---
if not st.session_state['autenticado']:
    st.title("🏗️ Euro Control Ingenieria")
    tab1, tab2, tab3 = st.tabs(["🔐 Iniciar Sesión", "📝 Registro", "📧 Recuperar y Cambiar Contraseña"])
    
    with tab1:
        u = st.text_input("Usuario o Cédula").strip()
        p = st.text_input("Contraseña", type="password").strip()
        recordar = st.checkbox("Recordar sesión en este equipo")
        if st.button("Ingresar"):
            res = supabase.table("usuarios").select("*").or_(f"usuario.eq.{u},cedula.eq.{u}").eq("clave", p).execute()
            if res.data:
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = res.data[0]['usuario']
                st.session_state['cargo_user'] = res.data[0].get('cargo', 'Técnico')
                if recordar:
                    cookie_manager.set("euro_user_session", res.data[0]['usuario'])
                st.rerun()
            else: st.error("Error: Credenciales no válidas.")

    with tab2:
        st.subheader("Registro de Nuevo Personal")
        nom_real = st.text_input("Nombre y Apellido Completo")
        user_alias = st.text_input("Cree un Nombre de Usuario (Ej: juan.perez)")
        car = st.selectbox("Cargo", ["Asistente de ingenieria", "Supervisor", "Ingeniero", "Técnico", "Arquitecto", "Operador de Planta", "Operador de Habitaciones", "Operador de Áreas Públicas", "Plomero", "Técnico de Ascensores", "Técnico Mecánica General", "Técnico Mec. Cocina Y Lavandería", "Otros"])
        ced = st.text_input("Cédula de Identidad")
        cor = st.text_input("Correo")
        cla = st.text_input("Clave de Acceso", type="password")
        cod = st.text_input("Código de Autorización", type="password")
        
        if st.button("Crear Usuario"):
            # Lógica de códigos: Si usa el de Jefes, se le marca como Admin automáticamente
            is_boss_code = (cod == CODIGO_REGISTRO_JEFES)
            is_staff_code = (cod == CODIGO_REGISTRO_ADMIN)
            
            if is_boss_code or is_staff_code:
                if user_alias and ced and cla:
                    # Si es código de jefe, agregamos (Admin) al nombre de usuario para el filtro de permisos
                    final_user_name = f"{user_alias} (Admin)" if is_boss_code else user_alias
                    
                    supabase.table("usuarios").insert({
                        "usuario": final_user_name, 
                        "cedula": ced, 
                        "correo": cor, 
                        "clave": cla,
                        "cargo": car # Guardamos el cargo
                    }).execute()
                    st.success(f"¡Registrado! Ahora puedes entrar con tu usuario o cédula.")
                else: st.warning("Por favor rellene Usuario, Cédula y Clave.")
            else: st.error("Código de autorización incorrecto.")

    with tab3:
        st.subheader("Gestión de Contraseña")
        m_rec = st.text_input("Correo registrado para verificar identidad")
        if st.button("Verificar Correo"):
            res = supabase.table("usuarios").select("*").eq("correo", m_rec).execute()
            if res.data:
                st.session_state['reset_user'] = res.data[0]['usuario']
                st.success(f"Usuario identificado: {res.data[0]['usuario']}")
                st.info(f"Contraseña actual: {res.data[0]['clave']}")
            else: st.error("Correo no encontrado.")
        
        if 'reset_user' in st.session_state:
            st.divider()
            nueva_p = st.text_input("Nueva Contraseña", type="password")
            confirm_p = st.text_input("Confirmar Nueva Contraseña", type="password")
            if st.button("Actualizar Contraseña"):
                if nueva_p == confirm_p and nueva_p != "":
                    supabase.table("usuarios").update({"clave": nueva_p}).eq("usuario", st.session_state['reset_user']).execute()
                    st.success("✅ Contraseña actualizada correctamente. Ya puede iniciar sesión.")
                    del st.session_state['reset_user']
                else: st.warning("Las contraseñas no coinciden o están vacías.")

else:
    # --- PANEL PRINCIPAL ---
    u_actual = st.session_state['usuario']
    cargo_actual = st.session_state.get('cargo_user', 'Técnico')
    
    # CORRECCIÓN DE ACCESO: Chequea si es admin por nombre o por el sufijo (
