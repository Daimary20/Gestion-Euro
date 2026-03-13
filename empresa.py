import streamlit as st
from datetime import datetime
from supabase import create_client, Client
from fpdf import FPDF
import extra_streamlit_components as stx

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3eG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"

if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(URL_SUPABASE, KEY_SUPABASE)

supabase = st.session_state.supabase

st.set_page_config(page_title="EURO Gestión Cloud", layout="wide", page_icon="🏗️")

# --- GESTIÓN DE SESIÓN PERSISTENTE ---
# Inicializamos el gestor de cookies fuera de funciones de caché para evitar el error de la imagen
cookie_manager = stx.CookieManager()

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# Intentar recuperar sesión de la cookie
if not st.session_state['autenticado']:
    user_saved = cookie_manager.get(cookie="euro_user_session")
    if user_saved:
        st.session_state['autenticado'] = True
        st.session_state['usuario'] = user_saved

# --- FUNCIÓN GENERAR PDF ---
def generar_pdf(lista_reportes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "EURO GESTION - REPORTE DE TRABAJOS", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Generado el: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(35, 8, "Fecha", 1, 0, "L", True)
    pdf.cell(45, 8, "Equipo", 1, 0, "L", True)
    pdf.cell(40, 8, "Tecnico", 1, 0, "L", True)
    pdf.cell(70, 8, "Detalles", 1, 1, "L", True)
    pdf.set_font("Arial", "", 9)
    for r in lista_reportes:
        pdf.cell(35, 8, str(r.get('fecha', ''))[:10], 1)
        pdf.cell(45, 8, str(r.get('equipo', ''))[:20], 1)
        pdf.cell(40, 8, str(r.get('tecnico', ''))[:15], 1)
        pdf.cell(70, 8, str(r.get('descripcion', ''))[:40], 1, 1)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 2. LÓGICA DE ACCESO ---
if not st.session_state['autenticado']:
    st.title("🏗️ EURO Control")
    tab1, tab2, tab3 = st.tabs(["🔐 Entrar", "📝 Registro", "📧 Recuperar"])
    
    with tab1:
        u = st.text_input("Usuario", key="u_login").strip()
        p = st.text_input("Clave", type="password", key="p_login").strip()
        recordar = st.checkbox("Recordarme en este dispositivo")
        
        if st.button("Iniciar Sesión"):
            try:
                res = supabase.table("usuarios").select("*").eq("usuario", u).eq("clave", p).execute()
                if res.data:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = u
                    if recordar:
                        cookie_manager.set("euro_user_session", u, key="set_cookie")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab2:
        nu = st.text_input("Nuevo Usuario", key="u_reg")
        ne = st.text_input("Correo", key="e_reg")
        np = st.text_input("Contraseña", type="password", key="p_reg")
        if st.button("Crear Cuenta"):
            try:
                supabase.table("usuarios").insert({"usuario": nu, "correo": ne, "clave": np}).execute()
                st.success("Cuenta creada")
            except Exception as e:
                st.error("Error al registrar")

    with tab3:
        email_b = st.text_input("Correo registrado", key="e_rec")
        if st.button("Recuperar"):
            try:
                res = supabase.table("usuarios").select("*").eq("correo", email_b).execute()
                if res.data:
                    st.info(f"Usuario: {res.data[0]['usuario']} | Clave: {res.data[0]['clave']}")
                else:
                    st.warning("No encontrado")
            except Exception as e:
                st.error("Error consulta")

else:
    # --- 3. APP PRINCIPAL ---
    st.sidebar.title("EURO Control")
    st.sidebar.write(f"👤 {st.session_state['usuario']}")
    
    if st.sidebar.button("🚪 Cerrar Sesión"):
        cookie_manager.delete("euro_user_session")
        st.session_state['autenticado'] = False
        st.rerun()

    menu = st.sidebar.radio("Menú", ["➕ Registrar Trabajo", "📋 Historial"])

    if menu == "➕ Registrar Trabajo":
        st.header("📝 Nuevo Registro de Trabajo")
        f_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        with st.form("f_trabajo", clear_on_submit=True):
            eq = st.text_input("Equipo")
            ar = st.text_input("Área")
            de = st.text_area("Detalles")
            f = st.file_uploader("Evidencia", type=["jpg","png","jpeg","mp4","mov"])
            if st.form_submit_button("Guardar Trabajo"):
                if eq and f:
                    try:
                        fname = f"{datetime.now().strftime('%Y%m%d%H%M')}_{f.name}"
                        supabase.storage.from_("evidencias").upload(fname, f.getvalue())
                        url = supabase.storage.from_("evidencias").get_public_url(fname)
                        supabase.table("reportes_euro").insert({
                            "fecha": f_actual, "tecnico": st.session_state['usuario'],
                            "area": ar, "equipo": eq, "descripcion": de, "url_multimedia": url
                        }).execute()
                        st.success("Trabajo guardado")
                    except Exception as e:
                        st.error("Error al guardar")
                else:
                    st.warning("Equipo y Evidencia son obligatorios")

    if menu == "📋 Historial":
        st.header("📋 Historial de Trabajos")
        busq = st.text_input("🔍 Buscar")
        try:
            res = supabase.table("reportes_euro").select("*").execute()
            if res.data:
                datos = res.data[::-1]
                if busq:
                    b = busq.lower()
                    datos = [r for r in datos if b in r['tecnico'].lower() or b in r['area'].lower() or b in (r['equipo'].lower() if r['equipo'] else "") or b in r['fecha'].lower()]
                
                if datos:
                    pdf_bytes = generar_pdf(datos)
                    st.download_button("📥 Descargar PDF", data=pdf_bytes, file_name="reporte.pdf", mime="application/pdf")

                for r in datos:
                    with st.expander(f"📅 {r['fecha']} | {r['equipo']}"):
                        st.write(f"👤 {r['tecnico']} | 📍 {r['area']}")
                        st.write(f"🛠️ {r['descripcion']}")
                        url = r['url_multimedia']
                        if url:
                            if ".mp4" in url.lower() or ".mov" in url.lower(): st.video(url)
                            else: st.image(url, use_container_width=True)
                        if st.button("Eliminar", key=f"d_{r['id']}"):
                            try:
                                supabase.table("reportes_euro").delete().eq("id", r['id']).execute()
                                st.rerun()
                            except:
                                st.error("Error al borrar")
            else:
                st.info("No hay datos")
        except Exception as e:
            st.error("Error al cargar datos")
