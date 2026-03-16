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

# --- FUNCIÓN PDF ACTUALIZADA ---
def generar_pdf(lista_reportes):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(280, 10, "EURO CONTROL INGENIERIA - REPORTE DE GESTION DETALLADO", ln=True, align="C")
    pdf.ln(5)
    
    # Encabezados
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(22, 8, "Fecha", 1, 0, "C", True)
    pdf.cell(35, 8, "Equipo", 1, 0, "C", True)
    pdf.cell(40, 8, "Responsable", 1, 0, "C", True)
    pdf.cell(30, 8, "Ubicacion", 1, 0, "C", True)
    pdf.cell(70, 8, "Descripcion Tarea", 1, 0, "C", True)
    pdf.cell(60, 8, "Seguimiento / Firma", 1, 0, "C", True) # Nueva columna firma
    pdf.cell(20, 8, "Estado", 1, 1, "C", True)
    
    pdf.set_font("Arial", "", 7)
    for r in lista_reportes:
        pdf.cell(22, 8, str(r.get('fecha', ''))[:10], 1)
        pdf.cell(35, 8, str(r.get('equipo', ''))[:22], 1)
        pdf.cell(40, 8, str(r.get('tecnico', ''))[:25], 1)
        pdf.cell(30, 8, str(r.get('area', ''))[:18], 1)
        
        desc = str(r.get('descripcion', '')).replace('\n', ' ')
        pdf.cell(70, 8, desc[:55], 1)
        
        # Mostrar quién firmó la revisión
        firma = r.get('comentario_supervisor', 'Sin revisión')
        pdf.cell(60, 8, str(firma)[:45], 1)
        
        pdf.cell(20, 8, str(r.get('estado', 'Pendiente')), 1, 1)
        
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- LOGIN Y REGISTRO ---
if not st.session_state['autenticado']:
    st.title("🏗️ Euro Control Ingenieria")
    tab1, tab2, tab3 = st.tabs(["🔐 Iniciar Sesión", "📝 Registro de Personal", "📧 Recuperar Cuenta"])
    
    with tab1:
        u = st.text_input("Usuario o Cédula", key="u_login").strip()
        p = st.text_input("Contraseña", type="password", key="p_login").strip()
        if st.button("Ingresar al Sistema"):
            res = supabase.table("usuarios").select("*").or_(f"usuario.eq.{u},cedula.eq.{u}").eq("clave", p).execute()
            if res.data:
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = res.data[0]['usuario']
                cookie_manager.set("euro_user_session", res.data[0]['usuario'])
                st.rerun()
            else:
                st.error("Datos incorrectos.")

    with tab2:
        st.subheader("Formulario de Registro")
        nombre_completo = st.text_input("Nombre y Apellido")
        cargo_area = st.selectbox("Cargo / Área Técnica", [
            "Operador de habitaciones", "Herrería", "Mecánica de cocina", 
            "Asistente", "Asistente de ingenieria", "Operador de planta", 
            "Jefe de departamento", "Ingeniero", "Arquitecto", "Supervisor", "Otros"
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
                    st.success("✅ ¡Registro Exitoso!")
                except:
                    st.error("Error: Cédula ya registrada.")
            else:
                st.error("Código de autorización inválido.")

    with tab3:
        st.subheader("Recuperación de Credenciales")
        email_buscar = st.text_input("Ingrese su correo registrado")
        if st.button("Consultar Datos"):
            res = supabase.table("usuarios").select("*").eq("correo", email_buscar).execute()
            if res.data:
                st.info(f"**Usuario:** {res.data[0]['usuario']}\n**Contraseña:** {res.data[0]['clave']}")
            else:
                st.warning("Correo no encontrado.")

else:
    # --- PANEL PRINCIPAL ---
    st.sidebar.title("Euro Control Ingenieria")
    st.sidebar.write(f"👤 **Usuario:**\n{st.session_state['usuario']}")
    
    u_actual = st.session_state['usuario']
    es_admin = any(x in u_actual for x in ["Supervisor", "Arquitecto", "Ingeniero", "Jefe", "Asistente", "Daimary Salas"])

    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        try: cookie_manager.delete("euro_user_session")
        except: pass
        st.rerun()

    menu_ops = ["➕ Registrar Actividad", "📋 Historial y Búsqueda"]
    if es_admin:
        menu_ops.append("👥 Gestión de Personal")
        
    menu = st.sidebar.radio("Navegación", menu_ops)

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
                        st.error("Error al guardar.")

    if menu == "📋 Historial y Búsqueda":
        st.header("📋 Historial de Reportes")
        busqueda = st.text_input("🔍 Buscar por Técnico, Área, Equipo...")
        
        res_db = supabase.table("reportes_euro").select("*").execute()
        if res_db.data:
            lista_datos = res_db.data[::-1]
            if busqueda:
                b = busqueda.lower()
                lista_datos = [r for r in lista_datos if b in str(r['tecnico']).lower() or b in str(r['area']).lower() or b in str(r['equipo']).lower()]

            st.download_button("📥 Descargar Reporte PDF Detallado", data=generar_pdf(lista_datos), file_name="euro_control_auditoria.pdf")

            for item in lista_datos:
                status = item.get('estado', 'Pendiente')
                color = "🟠" if status == "Pendiente" else "🟢" if status == "Confirmado" else "🔴"
                
                with st.expander(f"{color} {item['fecha']} | {item['equipo']}"):
                    st.write(f"👷 **Técnico:** {item['tecnico']}")
                    st.write(f"📍 **Ubicación:** {item['area']}")
                    st.write(f"📝 **Descripción:** {item['descripcion']}")
                    if item.get('comentario_supervisor'):
                        st.info(f"💬 **Revisión:** {item['comentario_supervisor']}")
                    
                    # SE MANTIENE IMAGEN/VIDEO EN LA APP
                    if item.get('url_multimedia'):
                        if ".mp4" in item['url_multimedia'].lower() or ".mov" in item['url_multimedia'].lower():
                            st.video(item['url_multimedia'])
                        else:
                            st.image(item['url_multimedia'], use_container_width=True)

                    if es_admin:
                        st.markdown("---")
                        comentario = st.text_input("Comentario / Observación", key=f"rev_{item['id']}")
                        c1, c2, c3 = st.columns([1,1,2])
                        
                        # AL CONFIRMAR U OBSERVAR, SE GUARDA LA "FIRMA" (QUIÉN LO HIZO)
                        firma_texto = f"{comentario} (Por: {st.session_state['usuario']})"
                        
                        if c1.button("✅ Confirmar", key=f"ok_{item['id']}"):
                            supabase.table("reportes_euro").update({"estado": "Confirmado", "comentario_supervisor": firma_texto}).eq("id", item['id']).execute()
                            st.rerun()
                        if c2.button("❌ Observar", key=f"no_{item['id']}"):
                            supabase.table("reportes_euro").update({"estado": "Observado", "comentario_supervisor": firma_texto}).eq("id", item['id']).execute()
                            st.rerun()
                        if c3.checkbox("Borrar reporte", key=f"del_chk_{item['id']}"):
                            if st.button("Confirmar Eliminación", key=f"btn_del_{item['id']}"):
                                supabase.table("reportes_euro").delete().eq("id", item['id']).execute()
                                st.rerun()

    if menu == "👥 Gestión de Personal":
        st.header("👥 Control de Usuarios")
        res_users = supabase.table("usuarios").select("*").execute()
        if res_users.data:
            for u in res_users.data:
                col_u, col_b = st.columns([3, 1])
                col_u.write(f"👤 **{u['usuario']}**")
                if u['usuario'] != st.session_state['usuario']:
                    if col_b.checkbox("Eliminar", key=f"chk_u_{u['id']}"):
                        if col_b.button("Confirmar Borrado", key=f"user_{u['id']}"):
                            supabase.table("usuarios").delete().eq("id", u['id']).execute()
                            st.rerun()
                st.divider()
