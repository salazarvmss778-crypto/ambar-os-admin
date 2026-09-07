import streamlit as st
import random, string, time
from datetime import datetime, timedelta
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="AMBAR OS - Admin", layout="wide", page_icon="👑")

ADMIN_PASSWORD = "Ambar2026!"
SUPABASE_URL = "https://rkduzcvvjbnapqmlqoey.supabase.co"
SUPABASE_KEY = "sb_publishable_TB-CnBcxWJp7exNCseQ7aA_8rKQzbBQ"
PRODUCTOS = ["DocuExtract Pro"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def generar_key():
    return f"AMBAR-{''.join(random.choices(string.ascii_uppercase+string.digits,k=4))}-{''.join(random.choices(string.ascii_uppercase+string.digits,k=4))}"

if "auth" not in st.session_state:
    st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 AMBAR OS Login")
    pwd = st.text_input("Password", type="password")
    if st.button("Entrar"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Mal")
    st.stop()

supabase = get_supabase()
st.title("👑 AMBAR OS - Panel")

# Cargar
try:
    res = supabase.table("licencias").select("*").order("fecha_creacion", desc=True).execute()
    licencias = res.data if res.data else []
except Exception as e:
    st.error(f"Error Supabase: {e}")
    licencias = []

c1,c2,c3 = st.columns(3)
c1.metric("Total Licencias", len(licencias))
c2.metric("Activas", len([l for l in licencias if l.get("activo")]))
c3.metric("Ingresos", f"${sum(l.get('precio',0) or 0 for l in licencias)}")

tab1, tab2 = st.tabs(["📋 Ver Licencias", "➕ Crear Nueva"])

with tab1:
    if licencias:
        df = pd.DataFrame(licencias)
        st.dataframe(df, use_container_width=True)
        st.divider()
        keys = [l["key"] for l in licencias]
        sel = st.selectbox("Selecciona licencia para administrar", keys)
        lic_sel = next((l for l in licencias if l["key"]==sel), None)
        if lic_sel:
            st.json(lic_sel)
            col1,col2,col3 = st.columns(3)
            if col1.button("Activar/Pausar"):
                supabase.table("licencias").update({"activo": not lic_sel["activo"]}).eq("key", sel).execute()
                st.rerun()
            if col2.button("Eliminar", type="primary"):
                supabase.table("licencias").delete().eq("key", sel).execute()
                st.rerun()
            if col3.button("+30 dias"):
                try:
                    nueva = datetime.strptime(lic_sel["expira"], "%Y-%m-%d") + timedelta(days=30)
                except:
                    nueva = datetime.now() + timedelta(days=30)
                supabase.table("licencias").update({"expira": nueva.strftime("%Y-%m-%d")}).eq("key", sel).execute()
                st.rerun()
    else:
        st.info("No hay licencias. Crea una en la otra pestaña")

with tab2:
    with st.form("crear", clear_on_submit=True):
        cliente = st.text_input("Cliente *")
        email = st.text_input("Email")
        empresa = st.text_input("Empresa")
        producto = st.selectbox("Producto", PRODUCTOS)
        plan = st.selectbox("Plan", ["Mensual","Anual","Vitalicio","Prueba 7 dias"])
        precio = st.number_input("Precio", value=299)
        max_disp = st.number_input("Max dispositivos", value=3, min_value=1)
        dias = st.number_input("Dias vigencia", value=30)
        submit = st.form_submit_button("GENERAR LICENCIA", type="primary", use_container_width=True)
        if submit:
            if not cliente:
                st.error("Falta cliente")
            else:
                nueva_key = generar_key()
                hoy = datetime.now()
                expira = hoy + timedelta(days=int(dias))
                nueva = {
                    "key": nueva_key,
                    "cliente": cliente,
                    "email": email,
                    "empresa": empresa,
                    "producto": producto,
                    "plan": plan,
                    "precio": int(precio),
                    "max_dispositivos": int(max_disp),
                    "dispositivos": [],
                    "activo": True,
                    "fecha_creacion": hoy.strftime("%Y-%m-%d"),
                    "expira": expira.strftime("%Y-%m-%d"),
                    "usos": 0,
                    "notas": ""
                }
                supabase.table("licencias").upsert(nueva).execute()
                st.success(f"✅ CREADA: {nueva_key}")
                st.code(nueva_key)
                st.balloons()
