import streamlit as st
import random, string, time
from datetime import datetime, timedelta
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="AMBAR OS - Admin", layout="wide", page_icon="👑")

ADMIN_PASSWORD = "Ambar2026!"
SUPABASE_URL = "https://rkduzcvvjbnapqmlqoey.supabase.co"
SUPABASE_KEY = "sb_publishable_TB-CnBcxWJp7exNCseQ7aA_8rKQzbBQ"
PRODUCTOS = ["DocuExtract Pro", "Otro Producto Futuro"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def generar_key():
    suf = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    suf2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"AMBAR-{suf}-{suf2}"

def cargar_db():
    try:
        supabase = get_supabase()
        res = supabase.table("licencias").select("*").order("fecha_creacion", desc=True).execute()
        return {row["key"]: row for row in res.data} if res.data else {}
    except Exception as e:
        st.error(f"Error conectando a Supabase: {e}")
        return {}

def guardar_row(row):
    supabase = get_supabase()
    return supabase.table("licencias").upsert(row).execute()

# --- LOGIN ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 AMBAR OS - Login")
    pwd = st.text_input("Contraseña Admin", type="password")
    if st.button("Entrar"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# --- APP ---
st.sidebar.title("AMBAR OS")
st.sidebar.success("✅ Conectado a Supabase")
st.sidebar.caption(SUPABASE_URL)
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.auth = False
    st.rerun()

st.title("👑 AMBAR OS - Panel Central")

db = cargar_db()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Licencias", len(db))
col2.metric("Activas", sum(1 for v in db.values() if v.get("activo")))
col3.metric("Ingresos", f"${sum(v.get('precio',0) or 0 for v in db.values())}")
col4.metric("Dispositivos", sum(len(v.get("dispositivos",[]) or []) for v in db.values()))

# Control de pestaña activa
if "tab_active" not in st.session_state:
    st.session_state.tab_active = 0

tab1, tab2, tab3 = st.tabs(["📋 Licencias", "➕ Crear Licencia", "📊 Analytics"])

with tab1:
    if db:
        df = pd.DataFrame(list(db.values()))
        cols_show = [c for c in ["key","cliente","empresa","producto","plan","precio","activo","expira","usos","max_dispositivos"] if c in df.columns]
        st.dataframe(df[cols_show], use_container_width=True, hide_index=True)
        st.divider()
        key_sel = st.selectbox("Selecciona Key para gestionar", list(db.keys()), key="key_sel")
        if key_sel:
            lic = db[key_sel]
            st.json(lic)
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("🔒 Pausar / Activar", key="pause"):
                lic["activo"] = not lic["activo"]
                guardar_row(lic)
                st.success(f"Ahora: {'Activa' if lic['activo'] else 'Pausada'}")
                time.sleep(1)
                st.rerun()
            if c2.button("🗑️ Eliminar", key="del"):
                get_supabase().table("licencias").delete().eq("key", key_sel).execute()
                st.success("Eliminada")
                time.sleep(1)
                st.rerun()
            if c3.button("➕ +30 días", key="ext"):
                try:
                    nueva = datetime.strptime(lic["expira"], "%Y-%m-%d") + timedelta(days=30)
                except:
                    nueva = datetime.now() + timedelta(days=30)
                lic["expira"] = nueva.strftime("%Y-%m-%d")
                guardar_row(lic)
                st.success(f"Nueva expiración: {lic['expira']}")
                time.sleep(0.5)
                st.rerun()
            if c4.button("📋 Copiar Key", key="copy"):
                st.code(lic["key"])
    else:
        st.warning("No hay licencias en Supabase. ¿Ejecutaste el SQL para crear la tabla y deshabilitar RLS?")
        st.code("""create table if not exists licencias (
  key text primary key,
  cliente text,
  email text,
  empresa text,
  producto text,
  plan text,
  precio int,
  max_dispositivos int,
  dispositivos jsonb default '[]'::jsonb,
  activo boolean default true,
  fecha_creacion text,
  expira text,
  usos int default 0,
  notas text
);
alter table licencias disable row level security;""", language="sql")

with tab2:
    with st.form("crear", clear_on_submit=True):
        cliente = st.text_input("Nombre Cliente*")
        email = st.text_input("Email")
        empresa = st.text_input("Empresa")
        producto = st.selectbox("Producto", PRODUCTOS)
        plan = st.selectbox("Plan", ["Mensual","Anual","Vitalicio","Prueba 7 días"])
        precio = st.number_input("Precio MXN", value=299)
        max_disp = st.number_input("Max Dispositivos", value=1, min_value=1)
        dias = st.number_input("Días de vigencia", value=30)
        notas = st.text_area("Notas")
        submit = st.form_submit_button("🚀 Generar y Guardar en Supabase")
        if submit:
            if not cliente:
                st.error("Pon nombre del cliente")
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
                    "notas": notas
                }
                try:
                    guardar_row(nueva)
                    st.success(f"✅ Licencia creada: {nueva_key}")
                    st.balloons()
                    st.code(f"Key: {nueva_key}\nCliente: {cliente}\nExpira: {expira.strftime('%Y-%m-%d')}")
                    st.info("Ve a la pestaña 📋 Licencias para verla - recargando en 2s...")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error guardando: {e}. ¿Ejecutaste el SQL en Supabase?")

with tab3:
    if db:
        df = pd.DataFrame(list(db.values()))
        st.bar_chart(df["producto"].value_counts())
        st.write("Próximos vencimientos")
        try:
            st.dataframe(df.sort_values("expira")[["key","cliente","expira","activo"]].head(20))
        except:
            st.dataframe(df)
    else:
        st.info("Crea licencias para ver analytics")