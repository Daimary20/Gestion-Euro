import streamlit as st
from datetime import datetime
from supabase import create_client, Client
from fpdf import FPDF
import extra_streamlit_components as stx

# --- CONFIGURACIÓN ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3eG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"
CODIGO_REGISTRO_ADMIN = "EURO2026" 

if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(URL_SUPABASE, KEY_SUPABASE)

supabase = st.session_state.supabase
st.set_page_config(page_title="Euro Control Ingenieria", layout="wide", page_icon="🏗️")

# --- GESTIÓN DE SESIÓN (COOKIES) ---
cookie_manager = stx.CookieManager()

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# Intento de recuperar sesión guardada
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
    pdf.set_font("Arial", "B", 12)
    pdf.cell(280, 10, "REPORTE DE GESTIÓN - EURO CONTROL INGENIERIA", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(25, 8, "Fecha", 1, 0, "C", True)
    pdf.cell(40, 8, "Equipo", 1, 0, "C", True)
    pdf.cell(35, 8, "Área", 1, 0, "C", True)
    pdf.cell(45, 8, "Responsable", 1, 0, "C", True)
    pdf.cell(85, 8, "Descripción", 1, 0, "C", True)
    pdf.cell(50, 8, "Seguimiento", 1, 1, "C", True)
    pdf.set_font("Arial", "", 7)
    for r in lista_reportes:
        pdf.cell(25, 8, str(r.get('fecha', ''))[:10], 1)
        pdf.cell(40, 8, str(r.get('equipo', ''))[:25], 1)
        pdf.cell(35, 8, str(r.get('area', ''))[:20], 1)
        pdf.cell(45, 8, str(r.get('tecnico', ''))[:25], 1)
        desc = str(r.get('descripcion', '')).replace('\n', ' ')
        pdf.cell(85, 8, desc[:60], 1)
        firma = r.get('comentario_supervisor', 'Pendiente')
        pdf.cell(50, 8, str(firma)[:35], 1, 1)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- INTERFAZ ---
if not st.session_state['autenticado']:
    st.title("🏗️ Euro Control Ingenieria")
    tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registro"])
    
    with tab1:
        u = st.text_input("Usuario o Cédula").strip()
        p = st.text_input("Contraseña", type="password").strip()
        recordar = st.checkbox("Recordar sesión en este dispositivo")
        if st.button("Ingresar"):
            res = supabase.table("usuarios").select("*").or_(f"usuario.eq.{u},cedula.eq.{u}").eq("clave", p).execute()
            if res.data:
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = res.data[0]['usuario']
                if recordar:
                    cookie_manager.set("euro_user_session", res.data[0]['usuario'])
                st.rerun()
            else: st.error("Error de acceso.")

    with tab2:
        st.subheader("Registro")
        nom = st.text_input("Nombre Completo")
        car = st.selectbox("Cargo", ["Asistente de ingenieria", "Supervisor", "Ingeniero", "Técnico", "Otros"])
        ced = st.text_input("Cédula")
        cor = st.text_input("Correo")
        cla = st.text_input("Clave", type="password")
        cod = st.text_input("Código Autorización", type="password")
        if st.button("Registrar Usuario"):
            if cod == CODIGO_REGISTRO_ADMIN:
                supabase.table("usuarios").insert({"usuario": f"{nom} - {car}", "cedula": ced, "correo": cor, "clave": cla}).execute()
                st.success("Registrado correctamente.")
            else: st.error("Código incorrecto.")

else:
    u_actual = st.session_state['usuario']
    # DAIMARY SALAS y CARGOS ALTOS tienen permisos administrativos
    es_admin = any(x in u_actual for x in ["Supervisor", "Arquitecto", "Ingeniero", "Jefe", "Asistente", "Daimary Salas"])

    st.sidebar.title("Euro Control")
    st.sidebar.write(f"Usuario: {u_actual}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['autenticado'] = False
        try: cookie_manager.delete("euro_user_session")
        except: pass
        st.rerun()

    menu = st.sidebar.radio("Navegación", ["➕ Actividad", "📋 Historial", "👥 Personal"] if es_admin else ["➕ Actividad", "📋 Historial"])

    if menu == "➕ Actividad":
        st.header("Nuevo Reporte")
        with st.form("f_act"):
            eq = st.text_input("Equipo / Máquina")
            ar = st.text_input("Área a la que pertenece")
            ds = st.text_area("Descripción de la tarea")
            ev = st.file_uploader("Evidencia", type=["jpg","png","jpeg","mp4","mov"])
            if st.form_submit_button("Guardar"):
                if eq and ev:
                    fn = f"{datetime.now().strftime('%H%M%S')}_{ev.name}"
                    supabase.storage.from_("evidencias").upload(fn, ev.getvalue())
                    url = supabase.storage.from_("evidencias").get_public_url(fn)
                    supabase.table("reportes_euro").insert({
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "tecnico": u_actual, "area": ar, "equipo": eq, "descripcion": ds, "url_multimedia": url, "estado": "Pendiente"
                    }).execute()
                    st.success("Reporte guardado.")

    if menu == "📋 Historial":
        st.header("Historial de Actividades")
        res = supabase.table("reportes_euro").select("*").execute()
        if res.data:
            datos = res.data[::-1]
            st.download_button("📥 Descargar PDF", data=generar_pdf(datos), file_name="reporte_euro.pdf")
            for i in datos:
                with st.expander(f"{i['fecha']} | {i['equipo']} ({i.get('area', 'Sin Área')})"):
                    st.write(f"**Área:** {i.get('area', 'No especificada')}")
                    st.write(f"**Técnico:** {i['tecnico']}")
                    st.write(f"**Descripción:** {i['descripcion']}")
                    if i['url_multimedia']:
                        if ".mp4" in i['url_multimedia'].lower(): st.video(i['url_multimedia'])
                        else: st.image(i['url_multimedia'], use_container_width=True)
                    
                    if es_admin:
                        st.divider()
                        obs = st.text_input("Observación", key=f"obs_{i['id']}")
                        firma = f"{obs} (Revisado por: {u_actual})"
                        c1, c2, c3 = st.columns(3)
                        if c1.button("✅ Confirmar", key=f"ok_{i['id']}"):
                            supabase.table("reportes_euro").update({"estado": "Confirmado", "comentario_supervisor": firma}).eq("id", i['id']).execute()
                            st.rerun()
                        if c2.button("❌ Observar", key=f"no_{i['id']}"):
                            supabase.table("reportes_euro").update({"estado": "Observado", "comentario_supervisor": firma}).eq("id", i['id']).execute()
                            st.rerun()
                        # NUEVA OPCIÓN PARA DAIMARY: Borrar reportes
                        if c3.checkbox("Eliminar este reporte", key=f"del_chk_{i['id']}"):
                            if st.button("Confirmar Borrado", key=f"btn_del_{i['id']}"):
                                supabase.table("reportes_euro").delete().eq("id", i['id']).execute()
                                st.rerun()

    if menu == "👥 Personal":
        st.header("Gestión de Usuarios")
        u_res = supabase.table("usuarios").select("*").execute()
        for us in u_res.data:
            c_u, c_b = st.columns([3, 1])
            c_u.write(f"👤 {us['usuario']}")
            if us['usuario'] != u_actual:
                if c_b.button("Eliminar", key=f"del_u_{us.get('id', us['usuario'])}"):
                    supabase.table("usuarios").delete().eq("usuario", us['usuario']).execute()
                    st.rerun()
            st.divider()
