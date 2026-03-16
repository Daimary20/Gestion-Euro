import streamlit as st
from datetime import datetime
from supabase import create_client, Client
from fpdf import FPDF
import extra_streamlit_components as stx

# --- CONFIGURACIÓN DE SUPABASE ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3eG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"
CODIGO_REGISTRO_ADMIN = "EURO2026" 

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
    except:
        pass

# --- FUNCIÓN PDF DE AUDITORÍA ---
def generar_pdf(lista_reportes):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(280, 10, "EURO CONTROL INGENIERIA - REPORTE DE GESTION DETALLADO", ln=True, align="C")
    pdf.ln(5)
    
    # Encabezados con Descripción y Seguimiento
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(22, 8, "Fecha", 1, 0, "C", True)
    pdf.cell(35, 8, "Equipo", 1, 0, "C", True)
    pdf.cell(40, 8, "Tecnico", 1, 0, "C", True)
    pdf.cell(30, 8, "Ubicacion", 1, 0, "C", True)
    pdf.cell(70, 8, "Descripcion Tarea", 1, 0, "C", True)
    pdf.cell(60, 8, "Seguimiento (Revision)", 1, 0, "C", True)
    pdf.cell(20, 8, "Estado", 1, 1, "C", True)
    
    pdf.set_font("Arial", "", 7)
    for r in lista_reportes:
        pdf.cell(22, 8, str(r.get('fecha', ''))[:10], 1)
        pdf.cell(35, 8, str(r.get('equipo', ''))[:22], 1)
        pdf.cell(40, 8, str(r.get('tecnico', ''))[:25], 1)
        pdf.cell(30, 8, str(r.get('area', ''))[:18], 1)
        
        desc = str(r.get('descripcion', '')).replace('\n', ' ')
        pdf.cell(70, 8, desc[:55], 1)
        
        # Firma de quién revisó
        firma = r.get('comentario_supervisor', 'Pendiente de revision')
        pdf.cell(60, 8, str(firma)[:45], 1)
        
        pdf.cell(20, 8, str(r.get('estado', 'Pendiente')), 1, 1)
        
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- INTERFAZ ---
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
            else:
                st.error("Credenciales invalidas.")

    with tab2:
        st.subheader("Registro de Personal")
        nombre = st.text_input("Nombre y Apellido")
        cargo = st.selectbox("Cargo", ["Asistente de ingenieria", "Supervisor", "Ingeniero", "Tecnico", "Herrería", "Mecánica", "Otros"])
        ci = st.text_input("Cedula")
        mail = st.text_input("Correo")
        pw = st.text_input("Contraseña de cuenta", type="password")
        ac = st.text_input("Codigo Admin", type="password")
        if st.button("Registrar"):
            if ac == CODIGO_REGISTRO_ADMIN:
                try:
                    supabase.table("usuarios").insert({"usuario": f"{nombre} - {cargo}", "cedula": ci, "correo": mail, "clave": pw}).execute()
                    st.success("Registrado.")
                except: st.error("Error en registro.")
            else: st.error("Codigo invalido.")

    with tab3:
        email_rec = st.text_input("Correo para recuperar")
        if st.button("Consultar"):
            res = supabase.table("usuarios").select("*").eq("correo", email_rec).execute()
            if res.data: st.info(f"Usuario: {res.data[0]['usuario']} | Clave: {res.data[0]['clave']}")

else:
    # --- PANEL LOGUEADO ---
    st.sidebar.title("Euro Control")
    u_actual = st.session_state['usuario']
    # DAIMARY SALAS y ASISTENTES tienen acceso administrativo
    es_admin = any(x in u_actual for x in ["Supervisor", "Arquitecto", "Ingeniero", "Jefe", "Asistente", "Daimary Salas"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['autenticado'] = False
        try: cookie_manager.delete("euro_user_session")
        except: pass
        st.rerun()

    menu = st.sidebar.radio("Menu", ["➕ Actividad", "📋 Historial", "👥 Personal"] if es_admin else ["➕ Actividad", "📋 Historial"])

    if menu == "➕ Actividad":
        st.header("Registrar Nueva Actividad")
        with st.form("reg"):
            eq = st.text_input("Equipo")
            ub = st.text_input("Ubicacion")
            ds = st.text_area("Descripcion")
            fl = st.file_uploader("Evidencia", type=["jpg","png","jpeg","mp4","mov"])
            if st.form_submit_button("Guardar"):
                if eq and fl:
                    fname = f"{datetime.now().strftime('%m%d%H%M')}_{fl.name}"
                    supabase.storage.from_("evidencias").upload(fname, fl.getvalue())
                    url = supabase.storage.from_("evidencias").get_public_url(fname)
                    supabase.table("reportes_euro").insert({
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "tecnico": u_actual, "area": ub, "equipo": eq, 
                        "descripcion": ds, "url_multimedia": url, "estado": "Pendiente"
                    }).execute()
                    st.success("Guardado.")

    if menu == "📋 Historial":
        st.header("Historial y Revision")
        busq = st.text_input("Buscar...")
        res = supabase.table("reportes_euro").select("*").execute()
        if res.data:
            datos = res.data[::-1]
            if busq:
                b = busq.lower()
                datos = [d for d in datos if b in str(d['tecnico']).lower() or b in str(d['equipo']).lower()]
            
            st.download_button("📥 Descargar Reporte PDF Detallado", data=generar_pdf(datos), file_name="auditoria_euro.pdf")

            for i in datos:
                col_st = "🟠" if i['estado'] == "Pendiente" else "🟢" if i['estado'] == "Confirmado" else "🔴"
                with st.expander(f"{col_st} {i['fecha']} | {i['equipo']}"):
                    st.write(f"**Técnico:** {i['tecnico']}")
                    st.write(f"**Descripción:** {i['descripcion']}")
                    if i.get('comentario_supervisor'):
                        st.info(f"💬 {i['comentario_supervisor']}")
                    
                    if i['url_multimedia']:
                        if ".mp4" in i['url_multimedia'].lower(): st.video(i['url_multimedia'])
                        else: st.image(i['url_multimedia'], use_container_width=True)

                    if es_admin:
                        st.divider()
                        rev_msg = st.text_input("Nota de revision", key=f"rm_{i['id']}")
                        c1, c2, c3 = st.columns(3)
                        # SE INCLUYE EL NOMBRE DE QUIÉN FIRMA
                        firma = f"{rev_msg} (Revisado por: {u_actual})"
                        if c1.button("✅ Confirmar", key=f"c_{i['id']}"):
                            supabase.table("reportes_euro").update({"estado":"Confirmado", "comentario_supervisor": firma}).eq("id", i['id']).execute()
                            st.rerun()
                        if c2.button("❌ Observar", key=f"o_{i['id']}"):
                            supabase.table("reportes_euro").update({"estado":"Observado", "comentario_supervisor": firma}).eq("id", i['id']).execute()
                            st.rerun()
                        if c3.checkbox("Borrar", key=f"b_{i['id']}"):
                            if st.button("Confirmar Borrado", key=f"bt_{i['id']}"):
                                supabase.table("reportes_euro").delete().eq("id", i['id']).execute()
                                st.rerun()

    if menu == "👥 Personal":
        st.header("Gestion de Usuarios")
        u_res = supabase.table("usuarios").select("*").execute()
        for us in u_res.data:
            c_u, c_b = st.columns([3, 1])
            c_u.write(f"👤 **{us.get('usuario', 'Sin nombre')}**")
            if us.get('usuario') != u_actual:
                # CORRECCIÓN DE KEYERROR USANDO .get() Y VERIFICACIÓN DE ID
                uid = us.get('id')
                if uid and c_b.checkbox("Eliminar", key=f"ch_{uid}"):
                    if c_b.button("Confirmo", key=f"bt_u_{uid}"):
                        supabase.table("usuarios").delete().eq("id", uid).execute()
                        st.rerun()
            st.divider()
