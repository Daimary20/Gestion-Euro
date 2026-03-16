import streamlit as st
from datetime import datetime
from supabase import create_client, Client
from fpdf import FPDF
import extra_streamlit_components as stx
import re

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
    user_saved = cookie_manager.get(cookie="euro_user_session")
    if user_saved:
        st.session_state['autenticado'] = True
        st.session_state['usuario'] = user_saved

# --- FUNCIONES AUXILIARES ---
def generar_pdf(lista_reportes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "EURO CONTROL INGENIERIA - REPORTE DE GESTION", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(30, 8, "Fecha", 1, 0, "L", True)
    pdf.cell(45, 8, "Equipo", 1, 0, "L", True)
    pdf.cell(45, 8, "Responsable", 1, 0, "L", True)
    pdf.cell(30, 8, "Estado", 1, 0, "L", True)
    pdf.cell(40, 8, "Ubicacion", 1, 1, "L", True)
    pdf.set_font("Arial", "", 8)
    for r in lista_reportes:
        pdf.cell(30, 8, str(r.get('fecha', ''))[:10], 1)
        pdf.cell(45, 8, str(r.get('equipo', ''))[:25], 1)
        pdf.cell(45, 8, str(r.get('tecnico', ''))[:25], 1)
        pdf.cell(30, 8, str(r.get('estado', 'Pendiente')), 1)
        pdf.cell(40, 8, str(r.get('area', ''))[:20], 1, 1)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- ACCESO Y SEGURIDAD ---
if not st.session_state['autenticado']:
    st.title("🏗️ Euro Control Ingenieria")
    # Se restauró la pestaña de Recuperar Cuenta
    tab1, tab2, tab3 = st.tabs(["🔐 Iniciar Sesión", "📝 Registro de Personal", "📧 Recuperar Cuenta"])
    
    with tab1:
        u = st.text_input("Usuario o Cédula", key="u_login").strip()
        p = st.text_input("Contraseña", type="password", key="p_login").strip()
        if st.button("Ingresar al Sistema"):
            try:
                res = supabase.table("usuarios").select("*").or_(f"usuario.eq.{u},cedula.eq.{u}").eq("clave", p).execute()
                if res.data:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = res.data[0]['usuario']
                    st.rerun()
                else:
                    st.error("Datos incorrectos.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

    with tab2:
        st.subheader("Formulario de Registro")
        nombre_completo = st.text_input("Nombre y Apellido")
        cargo_area = st.selectbox("Cargo / Área Técnica", [
            "Operador de habitaciones", "Herrería", "Mecánica de cocina", 
            "Asistente de ingenieria", "Operador de planta",
            "Jefe de departamento", "Arquitecto", "Supervisor", "Otros"
        ])
        cedula_id = st.text_input("Cédula de Identidad")
        correo_inst = st.text_input("Correo Electrónico")
        clave_acc = st.text_input("Contraseña", type="password")
        auth_code = st.text_input("Código de Autorización", type="password")
        
        if st.button("Registrar Nuevo Usuario"):
            if auth_code == CODIGO_REGISTRO_ADMIN:
                nombre_usuario_final = f"{nombre_completo} - {cargo_area}"
                try:
                    supabase.table("usuarios").insert({
                        "usuario": nombre_usuario_final, "cedula": cedula_id, 
                        "correo": correo_inst, "clave": clave_acc
                    }).execute()
                    st.success(f"✅ ¡Registro Exitoso como {cargo_area}!")
                except:
                    st.error("Error: Cédula ya registrada.")
            else:
                st.error("Código de autorización inválido.")

    with tab3:
        st.subheader("Recuperación de Credenciales")
        email_buscar = st.text_input("Ingrese su correo electrónico registrado")
        if st.button("Consultar Datos"):
            try:
                res = supabase.table("usuarios").select("*").eq("correo", email_buscar).execute()
                if res.data:
                    st.info(f"**Usuario:** {res.data[0]['usuario']}\n\n**Contraseña:** {res.data[0]['clave']}")
                else:
                    st.warning("Este correo no se encuentra en nuestra base de datos.")
            except:
                st.error("Ocurrió un error al consultar la base de datos.")

else:
    # --- PANEL PRINCIPAL ---
    st.sidebar.title("Euro Control Ingenieria")
    st.sidebar.write(f"👤 **Usuario:**\n{st.session_state['usuario']}")
    
    u_actual = st.session_state['usuario']
    es_admin_jerarquia = any(x in u_actual for x in ["Supervisor", "Arquitecto", "Ingeniero", "Jefe"])

    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    menu = st.sidebar.radio("Navegación", ["➕ Registrar Actividad", "📋 Historial y Revisión"])

    if menu == "➕ Registrar Actividad":
        st.header("📝 Registro de Trabajo")
        with st.form("form_registro", clear_on_submit=True):
            equipo_maq = st.text_input("Equipo")
            ubicacion_exacta = st.text_input("Ubicación")
            descripcion_tarea = st.text_area("Descripción")
            evidencia_file = st.file_uploader("Evidencia", type=["jpg","png","jpeg","mp4","mov"])
            
            if st.form_submit_button("Guardar Reporte"):
                if equipo_maq and evidencia_file:
                    try:
                        nombre_archivo = f"{datetime.now().strftime('%Y%m%d%H%M')}_{evidencia_file.name}"
                        supabase.storage.from_("evidencias").upload(nombre_archivo, evidencia_file.getvalue())
                        url_file = supabase.storage.from_("evidencias").get_public_url(nombre_archivo)
                        supabase.table("reportes_euro").insert({
                            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "tecnico": st.session_state['usuario'],
                            "area": ubicacion_exacta, "equipo": equipo_maq, 
                            "descripcion": descripcion_tarea, "url_multimedia": url_file,
                            "estado": "Pendiente"
                        }).execute()
                        st.success("✅ Actividad guardada.")
                    except:
                        st.error("Error al subir archivo.")

    if menu == "📋 Historial y Revisión":
        st.header("📋 Historial de Reportes")
        res_db = supabase.table("reportes_euro").select("*").execute()
        if res_db.data:
            lista_datos = res_db.data[::-1]
            st.download_button("📥 Descargar PDF", data=generar_pdf(lista_datos), file_name="reporte.pdf")

            for item in lista_datos:
                status = item.get('estado', 'Pendiente')
                color_tag = "🟠" if status == "Pendiente" else "🟢" if status == "Confirmado" else "🔴"
                
                with st.expander(f"{color_tag} {item['fecha']} | {item['equipo']} | {status}"):
                    st.write(f"👷 **Técnico:** {item['tecnico']}")
                    st.write(f"📝 **Descripción:** {item['descripcion']}")
                    if item.get('comentario_supervisor'):
                        st.info(f"💬 **Observación:** {item['comentario_supervisor']}")
                    
                    if item['url_multimedia']:
                        if ".mp4" in item['url_multimedia'].lower() or ".mov" in item['url_multimedia'].lower():
                            st.video(item['url_multimedia'])
                        else:
                            st.image(item['url_multimedia'], use_container_width=True)

                    if es_admin_jerarquia:
                        st.markdown("---")
                        comentario_input = st.text_input("Comentario de revisión", key=f"in_{item['id']}")
                        c1, c2, c3 = st.columns([1, 1, 2])
                        
                        if c1.button("✅ Confirmar", key=f"ok_{item['id']}"):
                            supabase.table("reportes_euro").update({"estado": "Confirmado", "comentario_supervisor": comentario_input}).eq("id", item['id']).execute()
                            st.rerun()
                            
                        if c2.button("❌ Observado", key=f"no_{item['id']}"):
                            supabase.table("reportes_euro").update({"estado": "Observado", "comentario_supervisor": comentario_input}).eq("id", item['id']).execute()
                            st.rerun()
                            
                        if c3.button("🗑️ Eliminar Reporte", key=f"del_{item['id']}"):
                            supabase.table("reportes_euro").delete().eq("id", item['id']).execute()
                            st.rerun()
        else:
            st.info("Sin reportes.")
