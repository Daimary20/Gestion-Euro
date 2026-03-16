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
    tab1, tab2, tab3 = st.tabs(["🔐 Iniciar Sesión", "📝 Registro de Personal", "📧 Ayuda"])
    
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
                    st.error("Datos incorrectos. Verifique su usuario o clave.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

    with tab2:
        st.subheader("Formulario de Registro")
        nombre_completo = st.text_input("Nombre y Apellido", placeholder="Ej: Juan Pérez")
        cargo_area = st.selectbox("Cargo / Área Técnica", [
            "Operador de Habitaciones", "Áreas Públicas", "Lavandería", 
            "Mantenimiento General", "Electricidad", "Plomería", "Supervisor de Ingeniería"
        ])
        cedula_id = st.text_input("Cédula de Identidad (Solo números)")
        correo_inst = st.text_input("Correo Electrónico")
        clave_acc = st.text_input("Cree una Contraseña (mín. 6 caracteres)", type="password")
        auth_code = st.text_input("Código de Autorización de la Empresa", type="password")
        
        if st.button("Registrar Nuevo Usuario"):
            if auth_code == CODIGO_REGISTRO_ADMIN:
                nombre_usuario_final = f"{nombre_completo} - {cargo_area}"
                try:
                    supabase.table("usuarios").insert({
                        "usuario": nombre_usuario_final, 
                        "cedula": cedula_id, 
                        "correo": correo_inst, 
                        "clave": clave_acc
                    }).execute()
                    st.success(f"✅ ¡Registro Exitoso! Bienvenido, {nombre_usuario_final}.")
                except:
                    st.error("Error: El número de cédula ya se encuentra registrado.")
            else:
                st.error("Código de autorización inválido.")

else:
    # --- PANEL PRINCIPAL ---
    st.sidebar.title("Euro Control Ingenieria")
    st.sidebar.write(f"👤 **Usuario Activo:**\n{st.session_state['usuario']}")
    
    # Verificación de rango de Supervisor
    es_supervisor = "Supervisor" in st.session_state['usuario']

    if st.sidebar.button("🚪 Cerrar Sesión Segura"):
        try:
            cookie_manager.delete("euro_user_session")
        except:
            pass
        st.session_state['autenticado'] = False
        st.rerun()

    menu = st.sidebar.radio("Navegación Principal", ["➕ Registrar Actividad", "📋 Historial y Revisión"])

    if menu == "➕ Registrar Actividad":
        st.header("📝 Registro de Trabajo Diario")
        with st.form("form_registro", clear_on_submit=True):
            equipo_maq = st.text_input("Equipo o Maquinaria intervenida")
            ubicacion_exacta = st.text_input("Ubicación / Área (Ej: Hab 402, Cocina)")
            descripcion_tarea = st.text_area("Descripción detallada del trabajo realizado")
            evidencia_file = st.file_uploader("Adjuntar Evidencia (Foto o Video)", type=["jpg","png","jpeg","mp4","mov"])
            
            if st.form_submit_button("Guardar Reporte"):
                if equipo_maq and evidencia_file:
                    try:
                        timestamp = datetime.now().strftime('%Y%m%d%H%M')
                        nombre_archivo = f"{timestamp}_{evidencia_file.name}"
                        supabase.storage.from_("evidencias").upload(nombre_archivo, evidencia_file.getvalue())
                        url_file = supabase.storage.from_("evidencias").get_public_url(nombre_archivo)
                        
                        supabase.table("reportes_euro").insert({
                            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "tecnico": st.session_state['usuario'],
                            "area": ubicacion_exacta, 
                            "equipo": equipo_maq, 
                            "descripcion": descripcion_tarea, 
                            "url_multimedia": url_file,
                            "estado": "Pendiente"
                        }).execute()
                        st.success("✅ Actividad registrada correctamente en la base de datos.")
                    except:
                        st.error("Error al procesar el archivo. Intente con una imagen más pequeña.")
                else:
                    st.warning("Por favor, complete el nombre del equipo y adjunte una evidencia.")

    if menu == "📋 Historial y Revisión":
        st.header("📋 Historial de Reportes")
        busqueda_global = st.text_input("🔍 Buscar por técnico, equipo o estado...")
        
        res_db = supabase.table("reportes_euro").select("*").execute()
        if res_db.data:
            lista_datos = res_db.data[::-1]
            
            if busqueda_global:
                bg = busqueda_global.lower()
                lista_datos = [r for r in lista_datos if bg in r['tecnico'].lower() or bg in r['equipo'].lower() or bg in r.get('estado', '').lower()]

            if lista_datos:
                st.download_button("📥 Descargar Reporte Consolidado (PDF)", 
                                 data=generar_pdf(lista_datos), 
                                 file_name=f"reporte_ingenieria_{datetime.now().strftime('%d_%m')}.pdf")

            for item in lista_datos:
                status = item.get('estado', 'Pendiente')
                # Indicadores visuales de estado
                color_tag = "🟠" if status == "Pendiente" else "🟢" if status == "Confirmado" else "🔴"
                
                with st.expander(f"{color_tag} {item['fecha']} | {item['equipo']} | {status}"):
                    col_info, col_media = st.columns([1, 1])
                    
                    with col_info:
                        st.write(f"👷 **Técnico:** {item['tecnico']}")
                        st.write(f"📍 **Ubicación:** {item['area']}")
                        st.write(f"📝 **Descripción:** {item['descripcion']}")
                        if item.get('comentario_supervisor'):
                            st.info(f"💬 **Nota del Supervisor:** {item['comentario_supervisor']}")
                    
                    with col_media:
                        if item['url_multimedia']:
                            if ".mp4" in item['url_multimedia'].lower() or ".mov" in item['url_multimedia'].lower():
                                st.video(item['url_multimedia'])
                            else:
                                st.image(item['url_multimedia'], use_container_width=True)

                    # PANEL EXCLUSIVO PARA SUPERVISORES
                    if es_supervisor:
                        st.markdown("---")
                        st.subheader("⚡ Panel de Supervisión")
                        comentario_input = st.text_input("Escribir observación o comentario", key=f"input_{item['id']}")
                        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
                        
                        if btn_col1.button("✅ Confirmar", key=f"btn_ok_{item['id']}"):
                            supabase.table("reportes_euro").update({
                                "estado": "Confirmado", 
                                "comentario_supervisor": comentario_input
                            }).eq("id", item['id']).execute()
                            st.rerun()
                            
                        if btn_col2.button("❌ Observado", key=f"btn_no_{item['id']}"):
                            supabase.table("reportes_euro").update({
                                "estado": "Observado", 
                                "comentario_supervisor": comentario_input
                            }).eq("id", item['id']).execute()
                            st.rerun()
                            
                        if btn_col3.button("🗑️ Eliminar Reporte", key=f"btn_del_{item['id']}"):
                            supabase.table("reportes_euro").delete().eq("id", item['id']).execute()
                            st.rerun()
        else:
            st.info("No se encontraron reportes registrados actualmente.")
