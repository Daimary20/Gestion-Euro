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
            if cod == CODIGO_REGISTRO_ADMIN:
                if user_alias and ced and cla:
                    supabase.table("usuarios").insert({
                        "usuario": user_alias, 
                        "cedula": ced, 
                        "correo": cor, 
                        "clave": cla,
                        "nombre_completo": f"{nom_real} - {car}"
                    }).execute()
                    st.success(f"¡Registrado! Ahora puedes entrar con tu usuario '{user_alias}' o con tu cédula.")
                else: st.warning("Por favor rellene Usuario, Cédula y Clave.")
            else: st.error("Código Admin incorrecto.")

    with tab3:
        st.subheader("Gestión de Contraseña")
        m_rec = st.text_input("Correo registrado para verificar identidad")
        if st.button("Verificar Correo"):
            res = supabase.table("usuarios").select("*").eq("correo", m_rec).execute()
            if res.data:
                st.session_state['reset_user'] = res.data[0]['usuario']
                st.success(f"Usuario identificado: {res.data[0]['usuario']}")
                st.info(f"Contraseña actual: {res.data[0]['clave']}")
            else:
                st.error("Correo no encontrado.")
        
        if 'reset_user' in st.session_state:
            st.divider()
            nueva_p = st.text_input("Nueva Contraseña", type="password")
            confirm_p = st.text_input("Confirmar Nueva Contraseña", type="password")
            if st.button("Actualizar Contraseña"):
                if nueva_p == confirm_p and nueva_p != "":
                    supabase.table("usuarios").update({"clave": nueva_p}).eq("usuario", st.session_state['reset_user']).execute()
                    st.success("✅ Contraseña actualizada correctamente. Ya puede iniciar sesión.")
                    del st.session_state['reset_user']
                else:
                    st.warning("Las contraseñas no coinciden o están vacías.")

else:
    # --- PANEL PRINCIPAL ---
    u_actual = st.session_state['usuario']
    es_admin = any(x in u_actual for x in ["Supervisor", "Arquitecto", "Ingeniero", "Jefe", "Asistente", "Daimary Salas"])

    st.sidebar.title("Euro Control")
    st.sidebar.write(f"👤 {u_actual}")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        try: cookie_manager.delete("euro_user_session")
        except: pass
        st.rerun()

    menu = st.sidebar.radio("Navegación", ["➕ Actividad", "📋 Historial", "👥 Personal"] if es_admin else ["➕ Actividad", "📋 Historial"])

    if menu == "➕ Actividad":
        st.header("📝 Nuevo Reporte de Actividad")
        with st.form("form_a"):
            col_a, col_b = st.columns(2)
            eq = col_a.text_input("Equipo / Máquina")
            ar = col_b.text_input("Área de pertenencia")
            ds = st.text_area("Descripción detallada")
            ev = st.file_uploader("Evidencia (Foto o Video)", type=["jpg","png","jpeg","mp4","mov"])
            if st.form_submit_button("Enviar Reporte"):
                if eq and ev:
                    fn = f"{datetime.now().strftime('%H%M%S')}_{ev.name}"
                    supabase.storage.from_("evidencias").upload(fn, ev.getvalue())
                    url = supabase.storage.from_("evidencias").get_public_url(fn)
                    supabase.table("reportes_euro").insert({
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "tecnico": u_actual, "area": ar, "equipo": eq, "descripcion": ds, "url_multimedia": url, "estado": "Pendiente"
                    }).execute()
                    st.success("✅ Reporte guardado con éxito.")

    if menu == "📋 Historial":
        st.header("📋 Panel de Seguimiento")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        busq = c1.text_input("🔍 Buscar por Área, Técnico o Equipo")
        mes_f = c2.selectbox("Mes", ["Todos"] + [f"{i:02d}" for i in range(1, 13)])
        año_f = c3.selectbox("Año", ["Todos"] + [str(y) for y in range(2024, 2027)])
        
        res = supabase.table("reportes_euro").select("*").execute()
        if res.data:
            datos = res.data[::-1]
            if busq:
                b = busq.lower()
                datos = [d for d in datos if b in str(d.get('area','')).lower() or b in str(d.get('tecnico','')).lower() or b in str(d.get('equipo','')).lower()]
            if mes_f != "Todos":
                datos = [d for d in datos if d.get('fecha','')[3:5] == mes_f]
            if año_f != "Todos":
                datos = [d for d in datos if d.get('fecha','')[6:10] == año_f]

            k1, k2, k3 = st.columns(3)
            k1.metric("Pendientes", len([d for d in datos if d['estado'] == "Pendiente"]))
            k2.metric("Confirmados", len([d for d in datos if d['estado'] == "Confirmado"]))
            k3.metric("Observados", len([d for d in datos if d['estado'] == "Observado"]))

            st.download_button("📥 Generar Reporte PDF", data=generar_pdf(datos), file_name="auditoria_euro.pdf")
            
            for i in datos:
                color = "🟠" if i['estado'] == "Pendiente" else "🟢" if i['estado'] == "Confirmado" else "🔴"
                with st.expander(f"{color} {i['fecha']} | {i['equipo']} - {i.get('area', 'N/A')}"):
                    st.write(f"**Técnico:** {i['tecnico']}")
                    st.write(f"**Descripción:** {i['descripcion']}")
                    if i.get('comentario_supervisor'):
                        st.info(f"🗨️ {i['comentario_supervisor']}")
                    if i['url_multimedia']:
                        if ".mp4" in i['url_multimedia'].lower(): st.video(i['url_multimedia'])
                        else: st.image(i['url_multimedia'], use_container_width=True)
                    
                    if es_admin:
                        st.divider()
                        obs = st.text_input("Comentario de revisión", key=f"o_{i['id']}")
                        firma = f"{obs} (Revisado por: {u_actual})"
                        ca, cb, cc = st.columns(3)
                        if ca.button("✅ Confirmar", key=f"ok_{i['id']}"):
                            supabase.table("reportes_euro").update({"estado": "Confirmado", "comentario_supervisor": firma}).eq("id", i['id']).execute()
                            st.rerun()
                        if cb.button("❌ Observar", key=f"no_{i['id']}"):
                            supabase.table("reportes_euro").update({"estado": "Observado", "comentario_supervisor": firma}).eq("id", i['id']).execute()
                            st.rerun()
                        if cc.checkbox("Eliminar", key=f"del_c_{i['id']}"):
                            if st.button("Confirmar Borrado", key=f"del_b_{i['id']}"):
                                supabase.table("reportes_euro").delete().eq("id", i['id']).execute()
                                st.rerun()

    if menu == "👥 Personal":
        st.header("👥 Gestión de Usuarios")
        u_res = supabase.table("usuarios").select("*").execute()
        for us in u_res.data:
            c_u, c_b = st.columns([3, 1])
            c_u.write(f"👤 {us['usuario']} (C.I: {us.get('cedula', 'N/A')})")
            if us['usuario'] != u_actual:
                if c_b.button("Eliminar", key=f"du_{us.get('id', us['usuario'])}"):
                    supabase.table("usuarios").delete().eq("usuario", us['usuario']).execute()
                    st.rerun()
            st.divider()
            
with st.sidebar:
    # st.image("logo_euro.png", width=150) # Si tienes un logo
    st.title("Euro Control")
    st.markdown(f"**Sesión activa:** {u_actual}")
    st.progress(100) # Una línea visual divisoria
    st.divider()
