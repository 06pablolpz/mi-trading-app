import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import calendar

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Life & Trading OS Cloud", layout="wide", page_icon="☁️")

# --- CONEXIÓN A GOOGLE SHEETS ---
# Nombre de tu hoja en Google Drive
SHEET_NAME = "Trading_Database"

def get_connection():
    # Definir el alcance (scope)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # Cargar credenciales desde Streamlit Secrets
    creds_dict = st.secrets["service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    # Conectar
    client = gspread.authorize(creds)
    return client

# --- GESTIÓN DE DATOS (NUEVA: CLOUD) ---
# Mapeo de nombres de pestañas en Google Sheets
TABS = {
    'journal': 'Journal',
    'accounts': 'Cuentas',
    'finance': 'Finanzas',
    'objectives': 'Objetivos',
    'subs': 'Suscripciones',
    'groups': 'Grupos'
}

# Columnas esperadas para inicializar si está vacío
COLS = {
    'journal': ['Fecha', 'Cuenta', 'Activo', 'Estrategia', 'Resultado', 'RR', 'PnL', 'Emociones', 'Screenshot', 'Notas'],
    'accounts': ['Nombre', 'Empresa', 'Tipo', 'Balance_Inicial', 'Balance_Actual', 'Balance_Objetivo', 'Dias_Objetivo', 'Costo', 'Estado', 'Fecha_Creacion'],
    'finance': ['Fecha', 'Tipo', 'Concepto', 'Monto'],
    'objectives': ['ID', 'Tarea', 'Tipo', 'Fecha_Limite', 'Estado', 'Target_Dinero'],
    'subs': ['Servicio', 'Monto', 'Dia_Renovacion'],
    'groups': ['Nombre_Grupo', 'Cuentas']
}

def load_data(key):
    client = get_connection()
    try:
        sh = client.open(SHEET_NAME)
        # Intentar seleccionar la pestaña, si no existe, crearla
        try:
            worksheet = sh.worksheet(TABS[key])
        except gspread.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=TABS[key], rows=100, cols=20)
            worksheet.append_row(COLS[key]) # Poner cabeceras
            return pd.DataFrame(columns=COLS[key])
            
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Si el df está vacío pero tiene columnas, asegurar que coincidan
        if df.empty:
            return pd.DataFrame(columns=COLS[key])
            
        # Convertir columnas numéricas que puedan venir como texto
        for col in df.columns:
            if col in ['PnL', 'RR', 'Monto', 'Balance_Inicial', 'Balance_Actual', 'Balance_Objetivo', 'Costo', 'Target_Dinero']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                
        return df
        
    except Exception as e:
        st.error(f"Error conectando a Google Sheets: {e}")
        return pd.DataFrame(columns=COLS[key])

def save_data(df, key):
    client = get_connection()
    try:
        sh = client.open(SHEET_NAME)
        worksheet = sh.worksheet(TABS[key])
        
        # Limpiar y reescribir (es lo más seguro para evitar desincronización)
        worksheet.clear()
        # Poner cabeceras y datos
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        
    except Exception as e:
        st.error(f"Error guardando en Google Sheets: {e}")

# --- CARGAR DATOS AL INICIO ---
# Usamos st.cache_data para no leer de Google en cada clic, solo cuando sea necesario
# (Aunque para edición en tiempo real, lo llamaremos directo)
df_journal = load_data('journal')
df_accounts = load_data('accounts')
df_finance = load_data('finance')
df_objectives = load_data('objectives')
df_subs = load_data('subs')
df_groups = load_data('groups')

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .kpi-card { background-color: var(--secondary-background-color); border-radius: 12px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; margin-bottom: 10px; border: 1px solid rgba(128, 128, 128, 0.2); }
    .kpi-title { color: var(--text-color); opacity: 0.7; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { font-size: 24px; font-weight: 800; color: var(--text-color); }
    .stProgress > div > div > div > div { background-color: #00C076; }
    .cal-header { font-weight: bold; text-align: center; margin-bottom: 5px; color: var(--text-color); opacity: 0.8; font-size: 0.9em; text-transform: uppercase; }
    .pnl-cell { height: 100px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.2); margin: 4px; background-color: var(--secondary-background-color); display: flex; flex-direction: column; justify-content: space-between; padding: 8px; transition: all 0.2s ease; }
    .pnl-cell:hover { transform: translateY(-2px); border-color: #00C076; }
    .cell-date { font-weight: bold; color: var(--text-color); opacity: 0.5; font-size: 0.9em; }
    .cell-pnl { font-weight: 900; font-size: 1.4em; text-align: center; align-self: center; margin-bottom: 10px; }
    .win-day { border: 1px solid #00C076; background-color: rgba(0, 192, 118, 0.1); }
    .loss-day { border: 1px solid #FF4D4D; background-color: rgba(255, 77, 77, 0.1); }
    .win-text { color: #00C076; } .loss-text { color: #FF4D4D; }
    .calendar-day-agenda { border: 1px solid rgba(128, 128, 128, 0.2); background-color: var(--secondary-background-color); height: 100px; padding: 5px; font-size: 12px; border-radius: 8px; margin: 2px; overflow-y: auto; color: var(--text-color); }
    .event-tag { padding: 2px 5px; border-radius: 4px; margin-bottom: 2px; font-size: 10px; color: white; display: block; font-weight: bold; }
    .evt-payout { background-color: #00C076; } .evt-bill { background-color: #FF4D4D; } .evt-task { background-color: #3B8ED0; }
    div.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# --- UTILS ---
def kpi_card(title, value, type="currency", color_logic=True):
    color_style = ""
    if color_logic and isinstance(value, (int, float)):
        if value > 0: color_style = "color: #00C076;"
        elif value < 0: color_style = "color: #FF4D4D;"
        else: color_style = "color: #F7B924;"
    display = f"${value:,.2f}" if type == "currency" else f"{value:.1f}%" if type == "percent" else f"{value}"
    st.markdown(f"""<div class="kpi-card"><div class="kpi-title">{title}</div><div class="kpi-value" style="{color_style}">{display}</div></div>""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("☁️ Trading OS")
st.sidebar.success("Conectado a Google Drive ✅")
menu = st.sidebar.radio("Navegación", ["📊 Dashboard", "🎯 Agenda", "🧠 Insights", "✅ Checklist", "📓 Diario (Multi)", "🏦 Cuentas", "💰 Finanzas"])

# ==============================================================================
# LOGICA DE PÁGINAS (MISMA QUE V11.1 PERO CON GUARDADO CLOUD)
# ==============================================================================

# 1. DASHBOARD
if menu == "📊 Dashboard":
    st.header("Visión General")
    # Meta
    target = 10000.0
    if not df_objectives.empty:
        meta_rows = df_objectives[df_objectives['Tipo'] == 'META_ANUAL']
        if not meta_rows.empty: target = float(meta_rows.iloc[0]['Target_Dinero'])
    
    payouts = 0.0
    if not df_finance.empty:
        payouts_df = df_finance[df_finance['Tipo'].astype(str).str.contains("INGRESO", na=False)]
        payouts = payouts_df['Monto'].sum()
        
    prog = min(max(payouts/target, 0.0), 1.0)
    st.subheader(f"🎯 Meta Payouts: ${target:,.0f}")
    st.progress(prog)
    st.caption(f"Llevas: ${payouts:,.2f}")
    
    with st.popover("Editar Meta"):
        nm = st.number_input("Nueva Meta", value=target)
        if st.button("Guardar Meta"):
            # Borrar anterior y guardar nueva
            df_objectives = df_objectives[df_objectives['Tipo'] != 'META_ANUAL']
            new_obj = pd.DataFrame([{'ID': 999, 'Tarea': 'Meta', 'Tipo': 'META_ANUAL', 'Fecha_Limite': str(date.today()), 'Estado': 'Active', 'Target_Dinero': nm}])
            df_objectives = pd.concat([df_objectives, new_obj], ignore_index=True)
            save_data(df_objectives, 'objectives')
            st.rerun()
            
    st.divider()
    if not df_journal.empty:
        pnl = df_journal['PnL'].sum()
        wins = len(df_journal[df_journal['Resultado']=='WIN'])
        wr = (wins/len(df_journal)*100) if len(df_journal)>0 else 0
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("PnL Operativo", pnl, "currency")
        with c2: kpi_card("Win Rate", wr, "percent")
        with c3: kpi_card("Trades", len(df_journal), "number", False)
        with c4: kpi_card("Avg RR", df_journal['RR'].mean(), "number", False)
        
        # Grafico
        df_journal['Fecha'] = pd.to_datetime(df_journal['Fecha'])
        daily = df_journal.groupby('Fecha')['PnL'].sum().reset_index()
        fig = px.bar(daily, x='Fecha', y='PnL', color='PnL', color_continuous_scale=['red', 'green'])
        st.plotly_chart(fig, use_container_width=True)

# 2. AGENDA
elif menu == "🎯 Agenda":
    st.header("Agenda & Objetivos")
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("obj"):
            task = st.text_input("Tarea")
            if st.form_submit_button("Añadir"):
                new = pd.DataFrame([{'ID': len(df_objectives)+1, 'Tarea': task, 'Tipo': 'Diario', 'Fecha_Limite': str(date.today()), 'Estado': 'Pendiente', 'Target_Dinero': 0}])
                df_objectives = pd.concat([df_objectives, new], ignore_index=True)
                save_data(df_objectives, 'objectives'); st.rerun()
        # Lista tareas
        tasks = df_objectives[df_objectives['Tipo'] != 'META_ANUAL']
        if not tasks.empty:
            st.dataframe(tasks[['Tarea', 'Estado']], hide_index=True)
            
    with c2:
        st.subheader("Calendario")
        # Renderizado simple del calendario actual
        cal = calendar.monthcalendar(datetime.now().year, datetime.now().month)
        cols = st.columns(7)
        dias = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
        for i, c in enumerate(cols): c.markdown(f"**{dias[i]}**")
        for week in cal:
            cols = st.columns(7)
            for i, d in enumerate(week):
                if d != 0:
                    cols[i].markdown(f"<div class='calendar-day-agenda'>{d}</div>", unsafe_allow_html=True)

# 3. INSIGHTS
elif menu == "🧠 Insights":
    st.header("Analítica")
    if not df_journal.empty:
        df = df_journal.copy()
        df['Dia'] = pd.to_datetime(df['Fecha']).dt.day_name()
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Por Día")
            st.bar_chart(df.groupby('Dia')['PnL'].sum())
        with c2:
            st.caption("Por Estrategia")
            st.bar_chart(df.groupby('Estrategia')['PnL'].sum())
            
# 4. CHECKLIST
elif menu == "✅ Checklist":
    st.header("Checklist Pre-Trade")
    strat = st.selectbox("Estrategia", ["RANGOS", "CANALES", "ESTRECHOS"])
    ok = False
    if strat == "RANGOS":
        if st.checkbox("3 Patas") and st.checkbox("Extremos") and st.checkbox("H2/L2"): ok = True
    if ok: st.success("GO!")

# 5. DIARIO
elif menu == "📓 Diario (Multi)":
    st.header("Diario de Trades")
    with st.expander("➕ Nuevo Trade"):
        with st.form("trade"):
            c1, c2 = st.columns(2)
            d = c1.date_input("Fecha")
            # Cuentas activas
            accs = df_accounts[df_accounts['Estado']=='Activa']['Nombre'].unique()
            who = c2.multiselect("Cuentas", accs)
            pnl = st.number_input("PnL ($)", step=10.0)
            res = st.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            strat = st.selectbox("Estrategia", ["RANGOS", "CANALES", "ESTRECHOS"])
            
            if st.form_submit_button("Guardar"):
                rows = []
                for a in who:
                    rows.append({
                        'Fecha': str(d), 'Cuenta': a, 'Activo': 'NQ', 'Estrategia': strat,
                        'Resultado': res, 'RR': 0, 'PnL': pnl, 'Emociones': '', 'Screenshot': '', 'Notas': ''
                    })
                df_journal = pd.concat([df_journal, pd.DataFrame(rows)], ignore_index=True)
                save_data(df_journal, 'journal'); st.success("Guardado en Nube"); st.rerun()
    
    # Editor
    edited = st.data_editor(df_journal, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Guardar Cambios Diario"):
        save_data(edited, 'journal'); st.success("Actualizado"); st.rerun()

# 6. CUENTAS
elif menu == "🏦 Cuentas":
    st.header("Mis Cuentas")
    with st.expander("➕ Crear Cuenta"):
        with st.form("acc"):
            n = st.text_input("Nombre")
            e = st.text_input("Empresa")
            bi = st.number_input("Balance Inicial", 50000.0)
            ba = st.number_input("Balance Actual", 50000.0)
            bo = st.number_input("Objetivo", 53000.0)
            if st.form_submit_button("Crear"):
                new = pd.DataFrame([{
                    'Nombre': n, 'Empresa': e, 'Tipo': 'Examen', 
                    'Balance_Inicial': bi, 'Balance_Actual': ba, 'Balance_Objetivo': bo, 
                    'Dias_Objetivo': 5, 'Costo': 0, 'Estado': 'Activa', 'Fecha_Creacion': str(date.today())
                }])
                df_accounts = pd.concat([df_accounts, new], ignore_index=True)
                save_data(df_accounts, 'accounts'); st.rerun()
                
    active = df_accounts[df_accounts['Estado'] == 'Activa']
    for i, row in active.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            c1.metric(row['Nombre'], f"${row['Balance_Actual']:,.2f}")
            tgt = row['Balance_Objetivo'] - row['Balance_Inicial']
            curr = row['Balance_Actual'] - row['Balance_Inicial']
            # Evitar div por cero
            pg = min(max(curr/tgt, 0.0), 1.0) if tgt != 0 else 0
            c2.progress(pg, "Objetivo")
            
            # Edicion rapida
            new_b = c3.number_input("Actualizar Saldo", value=float(row['Balance_Actual']), key=f"b_{i}")
            if c3.button("Update", key=f"u_{i}"):
                df_accounts.at[i, 'Balance_Actual'] = new_b
                save_data(df_accounts, 'accounts'); st.rerun()

# 7. FINANZAS
elif menu == "💰 Finanzas":
    st.header("Finanzas")
    edited_fin = st.data_editor(df_finance, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Guardar Finanzas"):
        save_data(edited_fin, 'finance'); st.success("Guardado"); st.rerun()
