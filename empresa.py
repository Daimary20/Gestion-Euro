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
       car = st.selectbox("Cargo", ["Asistente de ingenieria", "Supervisor", "Ingeniero", "Técnico", "Arquitecto", "Operador de Planta", "Operador de Habitaciones", "Operador de Áreas Públicas", "Plomero", "Técnico de Ascensores", "Técnico Mecánica General", "Técnico Mec. Cocina Y Lavandería", "Otros"])
       ced = st.text_input("Cédula de Identidad (Será su nombre de usuario)")
       cor = st.text_input("Correo")
       cla = st.text_input("Clave de Acceso", type="password")
       cod = st.text_input("Código de Autorización", type="password")
       
       if st.button("Crear Usuario"):
           if cod == CODIGO_REGISTRO_ADMIN:
               if ced and cla:
                   # Se usa la cédula como 'usuario' para simplificar
                   supabase.table("usuarios").insert({
                       "usuario": ced, 
                       "cedula": ced, 
                       "correo": cor, 
                       "clave": cla,
                       "nombre_completo": f"{nom_real} - {car}"
                   }).execute()
                   st.success(f"¡Registrado! Inicie sesión con su cédula: {ced}")
               else: st.warning("Por favor rellene Cédula y Clave.")
           else: st.error("Código Admin incorrecto.")

   with tab3:
       st.subheader("Gestión de Contraseña")
       m_rec = st.text_input("Correo registrado")
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
           if st.button("Actualizar Contraseña"):
               if nueva_p != "":
                   supabase.table("usuarios").update({"clave": nueva_p}).eq("usuario", st.session_state['reset_user']).execute()
                   st.success("✅ Contraseña actualizada.")
                   del st.session_state['reset_user']
               else: st.warning("La contraseña no puede estar vacía.")

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
       st.header("📝 Nuevo Reporte")
       with st.form("form_a"):
           eq = st.text_input("Equipo / Máquina")
           ar = st.text_input("Área")
           ds = st.text_area("Descripción")
           ev = st.file_uploader("Evidencia", type=["jpg","png","jpeg","mp4","mov"])
           if st.form_submit_button("Enviar"):
               if eq and ev:
                   fn = f"{datetime.now().strftime('%H%M%S')}_{ev.name}"
                   supabase.storage.from_("evidencias").upload(fn, ev.getvalue())
                   url = supabase.storage.from_("evidencias").get_public_url(fn)
                   supabase.table("reportes_euro").insert({
                       "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                       "tecnico": u_actual, "area": ar, "equipo": eq, "descripcion": ds, "url_multimedia": url, "estado": "Pendiente"
                   }).execute()
                   st.success("✅ Reporte guardado.")

   if menu == "📋 Historial":
       st.header("📋 Historial")
       res = supabase.table("reportes_euro").select("*").execute()
       if res.data:
           datos = res.data[::-1]
           for i in datos:
               color = "🟠" if i['estado'] == "Pendiente" else "🟢" if i['estado'] == "Confirmado" else "🔴"
               # Se usa una llave basada en fecha y equipo para evitar el KeyError: 'id'
               with st.expander(f"{color} {i['fecha']} | {i['equipo']}"):
                   st.write(f"**Técnico:** {i['tecnico']}")
                   if i['url_multimedia']:
                       st.image(i['url_multimedia'], use_container_width=True)
                   
                   if es_admin:
                       st.divider()
                       # Usamos la combinación de técnico y fecha como identificador único seguro
                       key_safe = f"{i['tecnico']}_{i['fecha']}".replace(" ", "_")
                       if st.button("Eliminar", key=f"del_{key_safe}"):
                           supabase.table("reportes_euro").delete().eq("fecha", i['fecha']).eq("tecnico", i['tecnico']).execute()
                           st.rerun()

   if menu == "👥 Personal":
       st.header("👥 Personal")
       u_res = supabase.table("usuarios").select("*").execute()
       for us in u_res.data:
           c_u, c_b = st.columns([3, 1])
           c_u.write(f"👤 {us['usuario']} (C.I: {us.get('cedula', 'N/A')})")
           if us['usuario'] != u_actual:
               # Eliminado el uso de us['id'] para evitar errores
               if c_b.button("Eliminar", key=f"du_{us['usuario']}"):
                   supabase.table("usuarios").delete().eq("usuario", us['usuario']).execute()
                   st.rerun()
           st.divider()
