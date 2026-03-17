import streamlit as st
from datetime import datetime
from supabase import create_client, Client
from fpdf import FPDF
import extra_streamlit_components as stx

# --- CONFIGURACIÓN ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3eG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"

# CÓDIGOS DE ACCESO
CODIGO_PERSONAL = "EURO2026"
CODIGO_JEFES = "ADMIN777" 

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
                st.session_state['usuario'] = res_u.data[0]['usuario']
                st.session_state['cargo'] = res_u.data[0].get('cargo', 'Personal')
    except: pass

# --- FUNCIÓN PDF ---
def generar_pdf(lista_reportes):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(280, 10, "REPORTE DE GESTIÓN - EURO CONTROL", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(240, 240, 240)
    headers = [("Fecha", 25), ("Equipo", 45), ("Área", 40), ("Responsable", 45), ("Descripción", 80)]
    for h, w in headers:
        pdf.cell(w, 8, h, 1, 0, "C", True)
    pdf.ln()
    pdf.set_font("Arial", "", 8)
    for r in lista_reportes:
        pdf.cell(25, 8, str(r.get('fecha', ''))[:10], 1)
        pdf.cell(45, 8, str(r.get('equipo', ''))[:30], 1)
        pdf.cell(40, 8, str(r.get('area', ''))[:25], 1)
        pdf.cell(45, 8, str(r.get('tecnico', ''))[:30], 1)
        pdf.cell(80, 8, str(r.get('descripcion', ''))[:60], 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- INTERFAZ DE ACCESO ---
if not st.session_state['autenticado']:
    st.title("🏗️ Euro Control Ingenieria")
    tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registro de Personal"])
    
    with tab1:
        u = st.text_input("Usuario o Cédula").strip()
        p = st.text_input("Contraseña", type="password").strip()
        if st.button("Ingresar"):
            res = supabase.table("usuarios").select("*").or_(f"usuario.eq.{u},cedula.eq.{u}").eq("clave", p).execute()
            if res.data:
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = res.data[0]['usuario']
                st.session_state['cargo'] = res.data[0].get('cargo', 'Personal')
                cookie_manager.set("euro_user_session", res.data[0]['usuario'])
                st.rerun()
            else: st.error("Credenciales incorrectas.")

    with tab2:
        st.subheader("Formulario de Registro")
        c_nom = st.text_input("Nombre Completo")
        c_ced = st.text_input("Cédula (Usuario)")
        c_car = st.selectbox("Seleccione su Cargo", ["Técnico", "Supervisor", "Ingeniero", "Arquitecto", "Operador de Planta", "Operador de Habitaciones", "Asistente", "Otros"])
        c_cor = st.text_input("Correo Electrónico")
        c_cla = st.text_input("Defina su Clave", type="password")
        c_cod = st.text_input("Código de Autorización Empresa", type="password")
        
        if st.button("Registrar Usuario"):
            es_jefe = (c_cod == CODIGO_JEFES)
            es_pers = (c_cod == CODIGO_PERSONAL)

            if es_jefe or es_pers:
                # Si es jefe, el nombre de usuario lleva la marca de admin interna
                user_db = f"{c_ced} (Admin)" if es_jefe else c_ced
                
                supabase.table("usuarios").insert({
                    "usuario": user_db, 
                    "cedula": c_ced, 
                    "correo": c_cor, 
                    "clave": c_cla,
                    "cargo": c_car  # AQUÍ SE GUARDA EL CARGO SELECCIONADO
                }).execute()
                st.success(f"✅ ¡Registrado como {c_car}! Ya puede iniciar sesión.")
            else:
                st.error("Código de autorización incorrecto.")

else:
    # --- PANEL PRINCIPAL ---
    u_actual = st.session_state['usuario']
    cargo_actual = st.session_state.get('cargo', 'Personal')
    
    # Lógica de privilegios
    es_admin = any(x in u_actual.lower() for x in ["daimary salas", "cmorales", "(admin)"])

    # Sidebar con información del perfil
    st.sidebar.title("Euro Control")
    st.sidebar.markdown(f"**Usuario:** {u_actual}")
    st.sidebar.info(f"💼 **Cargo:** {cargo_actual}") # AQUÍ SE REFLEJA EL CARGO EN LA INTERFAZ
    
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        cookie_manager.delete("euro_user_session")
        st.rerun()

    menu = st.sidebar.radio("Menú", ["➕ Actividad", "📋 Historial", "👥 Personal"] if es_admin else ["➕ Actividad", "📋 Historial"])

    if menu == "➕ Actividad":
        st.header("📝 Nuevo Reporte de Actividad")
        with st.form("registro_act"):
            eq = st.text_input("Equipo / Máquina")
            ar = st.text_input("Área")
            ds = st.text_area("Descripción del Trabajo")
            ev = st.file_uploader("Evidencia", type=["jpg","png","jpeg"])
            if st.form_submit_button("Guardar Reporte"):
                if eq and ar and ev:
                    fn = f"{datetime.now().strftime('%H%M%S')}_{ev.name}"
                    supabase.storage.from_("evidencias").upload(fn, ev.getvalue())
                    url = supabase.storage.from_("evidencias").get_public_url(fn)
                    supabase.table("reportes_euro").insert({
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "tecnico": f"{u_actual} ({cargo_actual})", # Se guarda con cargo para el historial
                        "area": ar, "equipo": eq, "descripcion": ds, "url_multimedia": url, "estado": "Pendiente"
                    }).execute()
                    st.success("✅ Reporte enviado correctamente.")

    if menu == "📋 Historial":
        st.header("📋 Seguimiento de Trabajos")
        res = supabase.table("reportes_euro").select("*").execute()
        if res.data:
            datos = res.data[::-1]
            st.download_button("📥 Descargar Reporte PDF", data=generar_pdf(datos), file_name="auditoria.pdf")
            for i in datos:
                with st.expander(f"{i['estado']} | {i['fecha']} | {i['equipo']}"):
                    st.write(f"**Responsable:** {i['tecnico']}")
                    st.write(f"**Descripción:** {i['descripcion']}")
                    if i['url_multimedia']: st.image(i['url_multimedia'], width=400)
                    
                    if es_admin:
                        obs = st.text_input("Comentario / Firma", key=f"f_{i['id']}")
                        if st.button("✅ Aprobar Trabajo", key=f"ap_{i['id']}"):
                            supabase.table("reportes_euro").update({"estado": "Confirmado", "comentario_supervisor": f"{obs} - Por: {u_actual}"}).eq("id", i['id']).execute()
                            st.rerun()

    if menu == "👥 Personal":
        st.header("👥 Gestión de Usuarios y Cargos")
        u_res = supabase.table("usuarios").select("*").execute()
        for us in u_res.data:
            c1, c2 = st.columns([3, 1])
            c1.write(f"👤 **{us['usuario']}** | 💼 Cargo: {us.get('cargo', 'N/A')}")
            if c2.button("Eliminar", key=f"del_{us['usuario']}"):
                supabase.table("usuarios").delete().eq("usuario", us['usuario']).execute()
                st.rerun()
            st.divider()
