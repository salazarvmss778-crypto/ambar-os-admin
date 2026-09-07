import streamlit as st
import json, os, uuid, random, string, time
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="AMBAR OS - Admin", layout="wide", page_icon="🔐")

# --- CONFIG ---
ADMIN_PASSWORD = "Ambar2026!"  # Cambiala aqui
DB_FILE = "licencias_db.json"
PRODUCTOS = ["DocuExtract Pro"]

def generar_key():
    suf = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    suf2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"AMBAR-{suf}-{suf2}"

def cargar_db():
    if not os.path.exists(DB_FILE):
        # Demo inicial
        demo = {
            "AMBAR-LOPEZ-1234": {"key": "AMBAR-LOPEZ-1234", "cliente": "Contador Lopez", "email": "lopez@conta.com", "empresa": "Lopez & Asoc", "producto": "DocuExtract Pro", "plan": "Mensual", "precio": 299, "max_dispositivos": 1, "dispositivos": ["DEV-A1B2C3"], "activo": True, "fecha_creacion": "2026-09-01", "expira": "2026-10-01", "usos": 142, "notas": "Cliente puntual"},
            "AMBAR-GARZA-5678": {"key": "AMBAR-GARZA-5678", "cliente": "Inmobiliaria Garza", "email": "garza@inmo.com", "empresa": "Garza Inmo", "producto": "DocuExtract Pro", "plan": "Anual", "precio": 2490, "max_dispositivos": 2, "dispositivos": [], "activo": True, "fecha_creacion": "2026-08-15", "expira": "2027-08-15", "usos": 89, "notas": "2 sucursales"},
            "AMBAR-PRUEBA": {"key": "AMBAR-PRUEBA", "cliente": "Prueba Victor", "email": "victor@test.com", "empresa": "AMBAR OS", "producto": "DocuExtract Pro", "plan": "Vitalicio", "precio": 0, "max_dispositivos": 3, "dispositivos": [], "activo": True, "fecha_creacion": "2026-09-06", "expira": "2030-01-01", "usos": 12, "notas": "Tu licencia de prueba"},
        }
        guardar_db(demo)
        return demo
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def guardar_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def check_expiracion(fecha_str):
    try:
        exp = datetime.strptime(fecha_str, "%Y-%m-%d")
        hoy = datetime.now()
        dias = (exp - hoy).days
        return dias
    except:
        return 999

# --- LOGIN ---
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False

if not st.session_state.admin_auth:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("## 🔐 AMBAR OS Admin")
        st.caption("Panel exclusivo de licencias")
        pwd = st.text_input("Contraseña admin", type="password")
        if st.button("Entrar", use_container_width=True, type="primary"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🟦 AMBAR OS")
    st.caption("License Manager v1.0")
    st.divider()
    menu = st.radio("Menú", ["Licencias", "Crear Licencia", "Productos", "Ajustes"], label_visibility="collapsed")
    st.divider()
    if st.button("Cerrar sesión"):
        st.session_state.admin_auth = False
        st.rerun()
    st.markdown("<p style='font-size:11px;color:gray'>DocuExtract Pro<br>1 producto activo</p>", unsafe_allow_html=True)

db = cargar_db()

# --- DASHBOARD KPIS ---
if menu == "Licencias":
    st.title("Gestión de Licencias")
    # KPIs
    total = len(db)
    activas = sum(1 for v in db.values() if v["activo"])
    ingresos = sum(v.get("precio",0) for v in db.values() if v["activo"])
    por_expirar = sum(1 for v in db.values() if 0 <= check_expiracion(v["expira"]) <= 7)
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Licencias Activas", f"{activas}/{total}")
    k2.metric("Ingresos Estimados", f"${ingresos} MXN")
    k3.metric("Dispositivos Amarrados", sum(len(v.get("dispositivos",[])) for v in db.values()))
    k4.metric("Por Expirar (7d)", por_expirar, delta_color="inverse")

    st.divider()
    
    # Filtros
    f1, f2, f3, f4 = st.columns([2,1,1,1])
    with f1:
        busqueda = st.text_input("🔍 Buscar por cliente, key o email", "")
    with f2:
        filtro_estado = st.selectbox("Estado", ["Todos", "Activos", "Inactivos", "Por expirar"])
    with f3:
        filtro_producto = st.selectbox("Producto", ["Todos"] + PRODUCTOS)
    with f4:
        st.write("")
        if st.button("🔄 Recargar", use_container_width=True):
            st.rerun()

    # Tabla
    df_data = []
    for k, v in db.items():
        if busqueda and busqueda.lower() not in (v["cliente"]+v["key"]+v.get("email","")).lower():
            continue
        if filtro_estado == "Activos" and not v["activo"]:
            continue
        if filtro_estado == "Inactivos" and v["activo"]:
            continue
        if filtro_estado == "Por expirar" and not (0 <= check_expiracion(v["expira"]) <= 7):
            continue
        if filtro_producto != "Todos" and v["producto"] != filtro_producto:
            continue
        
        dias = check_expiracion(v["expira"])
        estado_exp = f"Expira en {dias}d" if dias>=0 else f"Expirada hace {-dias}d"
        
        df_data.append({
            "KEY": v["key"],
            "CLIENTE": v["cliente"],
            "PRODUCTO": v["producto"],
            "PLAN": v["plan"],
            "ESTADO": "🟢 Activa" if v["activo"] else "🔴 Inactiva",
            "DISP": f"{len(v.get('dispositivos',[]))}/{v['max_dispositivos']}",
            "EXPIRA": v["expira"],
            "DIAS": estado_exp,
            "USOS": v.get("usos",0),
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Acciones Rápidas")
    # Seleccionar licencia para acciones
    if df_data:
        keys_list = [d["KEY"] for d in df_data]
        sel_key = st.selectbox("Selecciona licencia para gestionar", keys_list)
        if sel_key:
            lic = db[sel_key]
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                if st.button("⏸️ Pausar / Activar", use_container_width=True):
                    db[sel_key]["activo"] = not db[sel_key]["activo"]
                    guardar_db(db)
                    st.success(f"Licencia {'activada' if db[sel_key]['activo'] else 'pausada'}")
                    time.sleep(1)
                    st.rerun()
            with c2:
                if st.button("🔓 Resetear Dispositivo", use_container_width=True):
                    db[sel_key]["dispositivos"] = []
                    guardar_db(db)
                    st.success("Dispositivos liberados. Cliente puede entrar en nueva PC.")
                    time.sleep(1)
                    st.rerun()
            with c3:
                if st.button("📅 Extender 30 días", use_container_width=True):
                    try:
                        exp = datetime.strptime(lic["expira"], "%Y-%m-%d") + timedelta(days=30)
                        db[sel_key]["expira"] = exp.strftime("%Y-%m-%d")
                        guardar_db(db)
                        st.success(f"Nueva fecha: {db[sel_key]['expira']}")
                        time.sleep(1)
                        st.rerun()
                    except:
                        st.error("Error en fecha")
            with c4:
                if st.button("📋 Copiar Key", use_container_width=True):
                    st.code(lic["key"])
                    st.toast("Key copiada")
            with c5:
                if st.button("🗑️ Eliminar", use_container_width=True, type="primary"):
                    if st.session_state.get("confirm_del") == sel_key:
                        del db[sel_key]
                        guardar_db(db)
                        st.success("Eliminada")
                        st.session_state.confirm_del = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.session_state.confirm_del = sel_key
                        st.warning("Click de nuevo para confirmar eliminación")

            # Detalle
            with st.expander(f"Detalle de {sel_key}", expanded=True):
                dc1, dc2 = st.columns(2)
                with dc1:
                    st.json(lic)
                with dc2:
                    st.markdown(f"""
                    **Cliente:** {lic['cliente']}<br>
                    **Email:** {lic.get('email','-')}<br>
                    **Empresa:** {lic.get('empresa','-')}<br>
                    **Precio:** ${lic.get('precio',0)}<br>
                    **Dispositivos amarrados:** {', '.join(lic.get('dispositivos',[])) or 'Ninguno'}<br>
                    **Notas:** {lic.get('notas','-')}
                    """, unsafe_allow_html=True)

elif menu == "Crear Licencia":
    st.title("Crear Nueva Licencia")
    with st.form("crear_lic"):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Nombre del cliente *", placeholder="Ej: Contador Lopez")
            email = st.text_input("Email", placeholder="cliente@empresa.com")
            empresa = st.text_input("Empresa", placeholder="Lopez & Asociados")
            producto = st.selectbox("Producto", PRODUCTOS)
        with col2:
            plan = st.selectbox("Plan", ["Mensual", "Trimestral", "Anual", "Vitalicio", "Prueba 7 días"])
            max_disp = st.number_input("Máx. dispositivos", min_value=1, max_value=10, value=1, help="1 = 1 PC, no se puede compartir")
            precio = st.number_input("Precio MXN", min_value=0, value=299)
            dias_validez = st.selectbox("Validez", ["30 días", "90 días", "365 días", "Vitalicio (1000 días)", "Personalizado"])
        
        if dias_validez == "Personalizado":
            expira = st.date_input("Fecha expiración").strftime("%Y-%m-%d")
        else:
            mapa = {"30 días": 30, "90 días": 90, "365 días": 365, "Vitalicio (1000 días)": 1000}
            if plan == "Prueba 7 días":
                dias = 7
            else:
                dias = mapa.get(dias_validez, 30)
            expira = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")

        notas = st.text_area("Notas internas", placeholder="Ej: Cliente referido por Garza, pago por transferencia...")

        col_a, col_b = st.columns([1,3])
        with col_a:
            custom_key = st.text_input("Key personalizada (opcional)", placeholder="Se genera sola si lo dejas vacío")
        with col_b:
            st.caption(f"Expirará el: {expira}")

        submitted = st.form_submit_button("🔐 Generar Licencia", use_container_width=True, type="primary")
        
        if submitted:
            if not cliente:
                st.error("Nombre del cliente obligatorio")
            else:
                key = custom_key.strip().upper() if custom_key else generar_key()
                if key in db:
                    st.error("Esa key ya existe, usa otra")
                else:
                    db[key] = {
                        "key": key,
                        "cliente": cliente,
                        "email": email,
                        "empresa": empresa,
                        "producto": producto,
                        "plan": plan,
                        "precio": precio,
                        "max_dispositivos": max_disp,
                        "dispositivos": [],
                        "activo": True,
                        "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
                        "expira": expira,
                        "usos": 0,
                        "notas": notas
                    }
                    guardar_db(db)
                    st.success(f"¡Licencia creada! {key}")
                    st.code(key)
                    st.balloons()

elif menu == "Productos":
    st.title("Productos")
    st.info("Por ahora solo tienes DocuExtract Pro. Cuando crees una nueva herramienta, la agregas aquí y podrás asignarle licencias sin tocar código.")
    st.dataframe(pd.DataFrame([{"Producto": "DocuExtract Pro", "Licencias activas": sum(1 for v in db.values() if v["producto"]=="DocuExtract Pro"), "Precio base": "$299/mes", "Estado": "Activo"}]), use_container_width=True)
    st.markdown("### ➕ Agregar nuevo producto (futuro)")
    st.text_input("Nombre del nuevo producto", placeholder="Ej: Facturador Automático")
    st.button("Agregar producto (próximamente)")

elif menu == "Ajustes":
    st.title("Ajustes")
    st.markdown(f"""
    **Base de datos:** `{DB_FILE}` - {len(db)} licencias guardadas  
    **Producto actual:** DocuExtract Pro  
    **Admin password:** Cambiala en el código `ADMIN_PASSWORD`
    
    ### API para tus herramientas (próximamente)
    Para que DocuExtract y tus futuras apps validen licencias contra este panel, usarán:
    ```
    GET /api/verify?key=AMBAR-XXXX&product=DocuExtract Pro
    ```
    Esto ya está preparado. Cuando despliegues este admin en Render, tu DocuExtract solo hará una petición a este panel.
    
    ### Persistencia en Render
    En Render gratis, el archivo `{DB_FILE}` se borra con cada deploy. Solución:
    1. Ve a Render > Tu servicio > Disk > Add Disk (1GB, path /opt/render/project/src)
    2. O conecta Supabase (te paso el código)
    """)
    if st.button("📥 Descargar respaldo JSON"):
        st.download_button("Descargar licencias_db.json", data=json.dumps(db, indent=2), file_name="licencias_db_backup.json", mime="application/json")
