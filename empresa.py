import streamlit as st
from datetime import datetime
from supabase import create_client, Client
from fpdf import FPDF
import extra_streamlit_components as stx

# --- CONFIGURACIÓN ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3eG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"

# NUEVOS CÓDIGOS DE ACCESO
CODIGO_PERSONAL = "EURO2026"
CODIGO_JEFES = "ADMIN777" # Código exclusivo para Supervisor, Arquitecto e Ingeniero

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
            st.session_state['autenticado'] = True
            st.session_state['usuario'] = user_saved
    except: pass

# --- FUNCIÓN PDF ---
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
    tab1, tab2, tab3 = st.tabs(["🔐 Iniciar Sesión", "📝 Registro", "📧 Recuperar"])
    
    with tab1:
        u = st.text_input("Usuario o Cédula").strip()
        p = st.text_input("Contraseña", type="password").strip()
        if st.button("Ingresar"):
            res = supabase.table("usuarios").select("*").or_(f"usuario.eq.{u},cedula.eq.{u}").eq("clave", p).execute()
            if res.data:
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = res.data[0]['usuario']
                cookie_manager.set("euro_user_session", res.data[0]['usuario'])
                st.rerun()
            else: st.error("Error: Credenciales no válidas.")

    with tab2:
        st.subheader("Registro de Personal")
        nom_real = st.text_input("Nombre y Apellido")
        car = st.selectbox("Cargo", ["Técnico", "Supervisor", "Ingeniero", "Arquitecto", "Operador", "Otros"])
        ced = st.text_input("Cédula (Será su usuario)")
        cor = st.text_input("Correo")
        cla = st.text_input("Clave", type="password")
        cod = st.text_input("Código de Autorización", type="password")
        
        if st.button("Finalizar Registro"):
            # LÓGICA DE CÓDIGOS
            es_jefe = (cod == CODIGO_JEFES)
            es_personal = (cod == CODIGO_PERSONAL)

            if es_jefe or es_personal:
                # Si es jefe, añadimos una marca al nombre de usuario para que el sistema lo reconozca como admin
                final_user = f"{ced} (Admin)" if es_jefe else ced
                
                supabase.table("usuarios").insert({
                    "usuario": final_user, 
                    "cedula": ced, 
                    "correo": cor, 
                    "clave": cla
                }).execute()
                st.success(f"¡Registrado con éxito! Inicie sesión con su cédula: {ced}")
            else:
                st.error("Código de autorización inválido.")

    with tab3:
        st.subheader("Recuperación")
        m_rec = st.text_input("Correo registrado")
        if st.button("Verificar"):
            res = supabase.table("usuarios").select("*").eq("correo", m_rec).execute()
            if res.data: st.info(f"Su usuario es: {res.data[0]['usuario']} | Su clave es: {res.data[0]['clave']}")
            else: st.error("No encontrado.")

else:
    # --- PANEL PRINCIPAL ---
    u_actual = st.session_state['usuario']
    
    # Lógica de Admin: Acceso si es CMorales o si el usuario tiene la marca "(Admin)"
    es_admin = any(x in u_actual.lower() for x in ["daimary salas", "cmorales", "(admin)"])

    st.sidebar.title("Euro Control")
    st.sidebar.write(f"👤 {u_actual}")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        cookie_manager.delete("euro_user_session")
        st.rerun()

    menu = st.sidebar.radio("Navegación", ["➕ Actividad", "📋 Historial", "👥 Personal"] if es_admin else ["➕ Actividad", "📋 Historial"])

    if menu == "➕ Actividad":
        st.header("📝 Nuevo Reporte")
        with st.form("form_a"):
            eq = st.text_input("Equipo / Máquina")
            ar = st.text_input("Área")
            ds = st.text_area("Descripción")
            ev = st.file_uploader("Evidencia", type=["jpg","png","mp4"])
            if st.form_submit_button("Enviar"):
                if eq and ev:
                    fn = f"{datetime.now().strftime('%H%M%S')}_{ev.name}"
                    supabase.storage.from_("evidencias").upload(fn, ev.getvalue())
                    url = supabase.storage.from_("evidencias").get_public_url(fn)
                    supabase.table("reportes_euro").insert({
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "tecnico": u_actual, "area": ar, "equipo": eq, "descripcion": ds, "url_multimedia": url, "estado": "Pendiente"
                    }).execute()
                    st.success("Reporte enviado.")

    if menu == "📋 Historial":
        st.header("📋 Historial de Actividades")
        res = supabase.table("reportes_euro").select("*").execute()
        if res.data:
            datos = res.data[::-1]
            st.download_button("📥 PDF Auditoría", data=generar_pdf(datos), file_name="reporte.pdf")
            for i in datos:
                with st.expander(f"{i['estado']} | {i['fecha']} | {i['equipo']}"):
                    st.write(f"Técnico: {i['tecnico']}")
                    st.write(f"Descripción: {i['descripcion']}")
                    if i['url_multimedia']: st.image(i['url_multimedia'])
                    
                    if es_admin:
                        obs = st.text_input("Firma/Comentario", key=f"f_{i['id']}")
                        if st.button("✅ Aprobar", key=f"ap_{i['id']}"):
                            supabase.table("reportes_euro").update({"estado": "Confirmado", "comentario_supervisor": obs}).eq("id", i['id']).execute()
                            st.rerun()

    if menu == "👥 Personal":
        st.header("👥 Gestión de Usuarios")
        u_res = supabase.table("usuarios").select("*").execute()
        for us in u_res.data:
            st.write(f"👤 {us['usuario']} - C.I: {us['cedula']}")
            if st.button("Eliminar", key=f"del_{us['usuario']}"):
                supabase.table("usuarios").delete().eq("usuario", us['usuario']).execute()
                st.rerun()
