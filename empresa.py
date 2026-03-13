import streamlit as st
from datetime import datetime
from supabase import create_client, Client
from fpdf import FPDF # Asegúrate de instalarlo con pip install fpdf

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
URL_SUPABASE = "https://fhaxcedlmancswxnebjo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZoYXhjZWRsbWFuY3N3eG5lYmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDU0MzgsImV4cCI6MjA4ODkyMTQzOH0.CnbDYu92BTjqMFSf0CBunNoE8XIBSW_gJyo2Dr7auIs"

if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(URL_SUPABASE, KEY_SUPABASE)

supabase = st.session_state.supabase

st.set_page_config(page_title="EURO Gestión Cloud", layout="wide", page_icon="🏗️")

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- FUNCIÓN PARA GENERAR PDF ---
def generar_pdf(lista_reportes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "EURO GESTION CLOUD - REPORTE DE TRABAJOS", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
    pdf.ln(10)

    # Cabecera de tabla
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(35, 8, "Fecha", 1, 0, "C", True)
    pdf.cell(40, 8, "Equipo", 1, 0, "C", True)
    pdf.cell(40, 8, "Tecnico", 1, 0, "C", True)
    pdf.cell(75, 8, "Detalles", 1, 1, "C", True)

    # Contenido
    pdf.set_font("Arial", "", 9)
    for r in lista_reportes:
        # Limitar texto de descripción para que no se salga de la celda
        desc = (r['descripcion'][:45] + '..') if len(r['descripcion']) > 45 else r['descripcion']
        pdf.cell(35, 8, str(r['fecha']), 1)
        pdf.cell(40, 8, str(r['equipo']), 1)
        pdf.cell(40, 8, str(r['tecnico']), 1)
        pdf.cell(75, 8, desc, 1, 1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 2. LÓGICA DE ACCESO ---
if not st.session_state['autenticado']:
    st.title("🏗️ EURO Control")
    tab_login, tab_reg, tab_rec = st.tabs(["🔐 Iniciar Sesión", "📝 Registro", "📧 Recuperar"])
    
    with tab_login:
        u = st.text_input("Usuario", key="login_u").strip()
        p = st.text_input("Clave", type="password", key="login_p").strip()
        if st.button("Entrar"):
            try:
                res = supabase.table("usuarios").select("*").eq("usuario", u).eq("clave", p).execute()
                if res.data:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = u
                    st.rerun()
                else:
                    st.error("Usuario o clave incorrectos")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab_reg:
        nu = st.text_input("Nuevo Usuario")
        ne = st.text_input("Correo Electrónico")
        np = st.text_input("Contraseña", type="password")
        if st.button("Crear Cuenta"):
            try:
                supabase.table("usuarios").insert({"usuario": nu, "correo": ne, "clave": np}).execute()
                st.success("✅ Registro exitoso")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab_rec:
        email_busca = st.text_input("Correo electrónico registrado")
        if st.button("Consultar Clave"):
            try:
                res = supabase.table("usuarios").select("*").eq("correo", email_busca).execute()
                if res.data:
                    info = res.data[0]
                    st.info(f"Usuario: {info['usuario']} | Clave: {info['clave']}")
                else:
                    st.warning("Correo no encontrado")
            except Exception as e:
                st.error(f"Error: {e}")

else:
    # --- 3. APP PRINCIPAL ---
    st.sidebar.title("Menú Principal")
    st.sidebar.write(f"👤 Técnico: **{st.session_state['usuario']}**")
    
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    menu = st.sidebar.radio("Ir a:", ["➕ Registrar Trabajo", "📋 Historial de Trabajos"])

    if menu == "➕ Registrar Trabajo":
        st.header("📝 Registro de Trabajo Realizado")
        fecha_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        st.info(f"📅 Fecha: {fecha_now}")

        with st.form("form_trabajo", clear_on_submit=True):
            eq = st.text_input("Equipo / Maquinaria")
            ar = st.text_input("Área / Ubicación")
            de = st.text_area("Detalles del trabajo")
            f = st.file_uploader("Evidencia", type=["jpg","png","jpeg","mp4","mov"])
            
            if st.form_submit_button("Guardar"):
                if eq and f:
                    try:
                        fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{f.name}"
                        supabase.storage.from_("evidencias").upload(fname, f.getvalue())
                        url = supabase.storage.from_("evidencias").get_public_url(fname)
                        
                        supabase.table("reportes_euro").insert({
                            "fecha": fecha_now,
                            "tecnico": st.session_state['usuario'],
                            "area": ar, 
                            "equipo": eq, 
                            "descripcion": de, 
                            "url_multimedia": url
                        }).execute()
                        st.success("✅ Guardado")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Faltan datos obligatorios")

    if menu == "📋 Historial de Trabajos":
        st.header("📋 Historial de Trabajos")
        
        busqueda = st.text_input("🔍 Buscar por Técnico, Área, Equipo o Fecha")

        try:
            res_h = supabase.table("reportes_euro").select("*").execute()
            if res_h.data:
                datos = res_h.data[::-1]

                if busqueda:
                    b = busqueda.lower()
                    datos = [r for r in datos if 
                             b in r['tecnico'].lower() or 
                             b in r['area'].lower() or 
                             b in (r['equipo'].lower() if r['equipo'] else "") or
                             b in r['fecha'].lower()]

                # BOTÓN PDF
                if datos:
                    pdf_data = generar_pdf(datos)
                    st.download_button(
                        label="📥 Descargar Reporte PDF",
                        data=pdf_data,
                        file_name=f"reporte_euro_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )

                st.write(f"Resultados: **{len(datos)}**")
                
                for r in datos:
                    with st.expander(f"📅 {r['fecha']} | {r['equipo']} ({r['tecnico']})"):
                        st.write(f"**📍 Área:** {r['area']}")
                        st.write(f"**🛠️ Detalles:** {r['descripcion']}")
                        
                        if st.button("🗑️ Borrar", key=f"del_{r['id']}"):
                            try:
                                if r['url_multimedia']:
                                    nombre = r['url_multimedia'].split("/")[-1]
                                    supabase.storage.from_("evidencias").remove([nombre])
                                supabase.table("reportes_euro").delete().eq("id", r['id']).execute
