import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import calendar
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Life & Trading OS Cloud", layout="wide", page_icon="☁️")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 5rem; }
    .kpi-card {
        background-color: var(--secondary-background-color);
        border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
        margin-bottom: 15px; border: 1px solid rgba(128, 128, 128, 0.2);
        height: 100%; display: flex; flex-direction: column; justify-content: center;
    }
    .kpi-title {
        color: var(--text-color); opacity: 0.8; font-size: 14px;
        font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;
    }
    .kpi-value { font-size: 26px; font-weight: 800; color: var(--text-color); line-height: 1.2; }
    .stProgress > div > div > div > div { background-color: #00C076; }
    .cal-header { font-weight: bold; text-align: center; padding: 10px; opacity: 0.8; text-transform: uppercase; }
    .pnl-cell, .calendar-day-agenda {
        min-height: 110px; border: 1px solid rgba(128, 128, 128, 0.2); margin: 4px;
        background-color: var(--secondary-background-color); padding: 8px; border-radius: 10px;
        display: flex; flex-direction: column; justify-content: space-between;
    }
    .cell-date { font-weight: bold; opacity: 0.6; font-size: 1em; }
    .cell-pnl { font-weight: 900; font-size: 1.4em; text-align: center; margin: auto; }
    .win-day { border-top: 4px solid #00C076; background-color: rgba(0, 192, 118, 0.05); }
    .loss-day { border-top: 4px solid #FF4D4D; background-color: rgba(255, 77, 77, 0.05); }
    .win-text { color: #00C076; } .loss-text { color: #FF4D4D; }
    .event-tag { padding: 3px 6px; border-radius: 4px; margin-bottom: 2px; font-size: 10px; color: white; font-weight: bold; }
    .evt-bill { background-color: #FF4D4D; } .evt-task { background-color: #3B8ED0; }
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN GOOGLE SHEETS ---
SHEET_NAME = "Trading_Database"

@st.cache_resource
def get_connection():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = st.secrets["service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# --- GESTIÓN DE DATOS ---
TABS = {'journal': 'Journal', 'accounts': 'Cuentas', 'finance': 'Finanzas', 'objectives': 'Objetivos', 'subs': 'Suscripciones', 'groups': 'Grupos'}
COLS = {
    'journal': ['Fecha', 'Cuenta', 'Activo', 'Estrategia', 'Resultado', 'RR', 'PnL', 'Emociones', 'Screenshot', 'Notas'],
    'accounts': ['Nombre', 'Empresa', 'Tipo', 'Balance_Inicial', 'Balance_Actual', 'Balance_Objetivo', 'Dias_Objetivo', 'Costo', 'Estado', 'Fecha_Creacion'],
    'finance': ['Fecha', 'Tipo', 'Concepto', 'Monto'],
    'objectives': ['ID', 'Tarea', 'Tipo', 'Fecha_Limite', 'Estado', 'Target_Dinero'],
    'subs': ['Servicio', 'Monto', 'Dia_Renovacion'],
    'groups': ['Nombre_Grupo', 'Cuentas']
}

@st.cache_data(ttl=60)
def load_data(key):
    client = get_connection()
    try:
        sh = client.open(SHEET_NAME)
        try: worksheet = sh.worksheet(TABS[key])
        except: 
            worksheet = sh.add_worksheet(title=TABS[key], rows=100, cols=20)
            worksheet.append_row(COLS[key])
            return pd.DataFrame(columns=COLS[key])
        
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty: return pd.DataFrame(columns=COLS[key])
        
        # Convertir números
        for col in df.columns:
            if col in ['PnL', 'RR', 'Monto', 'Balance_Inicial', 'Balance_Actual', 'Balance_Objetivo', 'Costo', 'Target_Dinero', 'Dias_Objetivo']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        return df
    except: return pd.DataFrame(columns=COLS[key])

def save_data(df, key):
    client = get_connection()
    try:
        sh = client.open(SHEET_NAME)
        ws = sh.worksheet(TABS[key])
        ws.clear()
        ws.update([df.columns.values.tolist()] + df.values.tolist())
        st.cache_data.clear()
    except Exception as e: st.error(f"Error al guardar: {e}")

# Carga inicial
df_journal = load_data('journal')
df_accounts = load_data('accounts')
df_finance = load_data('finance')
df_objectives = load_data('objectives')
df_subs = load_data('subs')
df_groups = load_data('groups')

# --- UTILS ---
def kpi_card(title, value, type="currency"):
    color = "#00C076" if value > 0 else "#FF4D4D" if value < 0 else "#F7B924"
    fmt = f"${value:,.2f}" if type=="currency" else f"{value:.1f}%" if type=="percent" else f"{value}"
    st.markdown(f"""<div class="kpi-card"><div class="kpi-title">{title}</div><div class="kpi-value" style="color:{color}">{fmt}</div></div>""", unsafe_allow_html=True)

# --- NAVEGACIÓN ---
st.sidebar.title("☁️ Trading OS")
st.sidebar.caption("✅ Conectado a Google Drive")
if st.sidebar.button("🔄 Sincronizar"): st.cache_data.clear(); st.rerun()
menu = st.sidebar.radio("Ir a:", ["📊 Dashboard", "🎯 Agenda", "🧠 Insights", "✅ Checklist", "📓 Diario (Multi)", "🏦 Cuentas", "💰 Finanzas"])

# ==============================================================================
# 1. DASHBOARD
# ==============================================================================
if menu == "📊 Dashboard":
    st.header("Visión General")
    target = 10000.0
    if not df_objectives.empty:
        meta = df_objectives[df_objectives['Tipo']=='META_ANUAL']
        if not meta.empty: target = float(meta.iloc[0]['Target_Dinero'])
    
    payouts = 0.0
    if not df_finance.empty:
        p_df = df_finance[df_finance['Tipo'].astype(str).str.contains("INGRESO", na=False)]
        payouts = p_df['Monto'].sum()
    
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.subheader(f"🎯 Meta Payouts: ${target:,.0f}")
        c1.progress(min(max(payouts/target, 0.0), 1.0))
        c1.caption(f"Retirado: **${payouts:,.2f}** | Falta: **${target-payouts:,.2f}**")
        with c2:
            if st.button("Editar Meta"):
                with st.form("m_f"):
                    nm = st.number_input("Nuevo Objetivo", value=target)
                    if st.form_submit_button("Guardar"):
                        df_objectives = df_objectives[df_objectives['Tipo'] != 'META_ANUAL']
                        # CORRECCIÓN DE ERROR: Usamos un diccionario para evitar errores de sintaxis en líneas largas
                        new_meta = {
                            'ID': 999, 
                            'Tarea': 'Meta', 
                            'Tipo': 'META_ANUAL', 
                            'Fecha_Limite': str(date.today()), 
                            'Estado': 'Active', 
                            'Target_Dinero': nm
                        }
                        df_objectives = pd.concat([df_objectives, pd.DataFrame([new_meta])], ignore_index=True)
                        save_data(df_objectives, 'objectives'); st.rerun()

    st.markdown("---")
    if not df_journal.empty:
        pnl = df_journal['PnL'].sum()
        wins = len(df_journal[df_journal['Resultado']=='WIN'])
        wr = (wins/len(df_journal)*100) if len(df_journal)>0 else 0
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("PnL Operativo", pnl)
        with c2: kpi_card("Win Rate", wr, "percent")
        with c3: kpi_card("Trades", len(df_journal), "number")
        with c4: kpi_card("Avg RR", df_journal['RR'].mean(), "number")
        
        df_journal['Fecha'] = pd.to_datetime(df_journal['Fecha'])
        daily = df_journal.groupby('Fecha')['PnL'].sum().reset_index()
        fig = px.area(daily, x='Fecha', y='PnL', template="plotly_dark")
        fig.update_traces(line_color='#00C076', fillcolor='rgba(0,192,118,0.1)')
        st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# 2. AGENDA
# ==============================================================================
elif menu == "🎯 Agenda":
    st.header("Agenda")
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("add_obj"):
            t = st.text_input("Tarea")
            if st.form_submit_button("Añadir"):
                new = pd.DataFrame([{'ID': len(df_objectives)+1, 'Tarea': t, 'Tipo': 'Diario', 'Fecha_Limite': str(date.today()), 'Estado': 'Pendiente', 'Target_Dinero': 0}])
                df_objectives = pd.concat([df_objectives, new], ignore_index=True)
                save_data(df_objectives, 'objectives'); st.rerun()
        
        st.subheader("Pendientes")
        tasks = df_objectives[(df_objectives['Tipo']!='META_ANUAL') & (df_objectives['Estado']!='Hecho')]
        if not tasks.empty:
            for i, r in tasks.iterrows():
                if st.checkbox(r['Tarea'], key=f"t_{i}"):
                    df_objectives.at[i, 'Estado'] = 'Hecho'
                    save_data(df_objectives, 'objectives'); st.rerun()
        else: st.info("Todo hecho ✅")

    with c2:
        st.subheader("Calendario")
        cal = calendar.monthcalendar(datetime.now().year, datetime.now().month)
        cols = st.columns(7)
        dias = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
        for i, c in enumerate(cols): c.markdown(f"<div class='cal-header'>{dias[i]}</div>", unsafe_allow_html=True)
        for week in cal:
            cols = st.columns(7)
            for i, d in enumerate(week):
                if d!=0:
                    evts = ""
                    for _, s in df_subs.iterrows():
                        if int(s['Dia_Renovacion']) == d: evts += f"<span class='event-tag evt-bill'>{s['Servicio']}</span>"
                    cols[i].markdown(f"<div class='calendar-day-agenda'><div class='cell-date'>{d}</div>{evts}</div>", unsafe_allow_html=True)
                else: cols[i].markdown("<div style='min-height:110px'></div>", unsafe_allow_html=True)

# ==============================================================================
# 3. INSIGHTS
# ==============================================================================
elif menu == "🧠 Insights":
    st.header("Analítica")
    if df_journal.empty: st.info("Registra trades para ver datos.")
    else:
        df = df_journal.copy()
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df['Dia'] = df['Fecha'].dt.day_name()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("PnL por Día")
            st.plotly_chart(px.bar(df.groupby('Dia')['PnL'].sum().reset_index(), x='Dia', y='PnL', color='PnL', color_continuous_scale=['red', 'green']), use_container_width=True)
        with c2:
            st.subheader("Estrategias")
            st.plotly_chart(px.box(df, x='Estrategia', y='PnL'), use_container_width=True)

# ==============================================================================
# 4. CHECKLIST
# ==============================================================================
elif menu == "✅ Checklist":
    st.header("Sala de Ejecución")
    strat = st.selectbox("Estrategia", ["RANGOS", "CANALES", "ESTRECHOS"])
    ok = False
    if strat == "RANGOS":
        if st.checkbox("3 Patas") and st.checkbox("Extremo") and st.checkbox("H2/L2"): ok = True
    elif strat == "CANALES":
        if st.checkbox("Tendencia") and st.checkbox("Pullback") and st.checkbox("Stop"): ok = True
    if ok: st.success("✅ SETUP VALIDO")

# ==============================================================================
# 5. DIARIO
# ==============================================================================
elif menu == "📓 Diario (Multi)":
    st.header("Diario")
    with st.expander("➕ NUEVO TRADE", expanded=True):
        mode = st.radio("Modo:", ["Cuenta Única", "Grupo"], horizontal=True)
        with st.form("trade"):
            c1, c2 = st.columns(2)
            d = c1.date_input("Fecha")
            targets = []
            if mode == "Cuenta Única":
                accs = df_accounts[df_accounts['Estado']=='Activa']['Nombre'].unique()
                sel = c2.selectbox("Cuenta", accs if len(accs)>0 else ["General"])
                targets = [sel]
            else:
                grps = df_groups['Nombre_Grupo'].unique()
                sel = c2.selectbox("Grupo", grps if len(grps)>0 else [])
                if len(grps)>0: targets = df_groups[df_groups['Nombre_Grupo']==sel]['Cuentas'].values[0].split(',')
            
            c3, c4, c5 = st.columns(3)
            pnl = c3.number_input("PnL ($)", step=10.0)
            res = c4.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            strat = c5.selectbox("Estrategia", ["RANGOS", "CANALES", "OTRO"])
            
            if st.form_submit_button("Guardar"):
                rows = []
                for t in targets:
                    rows.append({'Fecha': str(d), 'Cuenta': t.strip(), 'Activo': 'NQ', 'Estrategia': strat, 'Resultado': res, 'RR': 0, 'PnL': pnl, 'Emociones': '', 'Screenshot': '', 'Notas': ''})
                df_journal = pd.concat([df_journal, pd.DataFrame(rows)], ignore_index=True)
                save_data(df_journal, 'journal'); st.success("Guardado"); st.rerun()

    st.subheader(f"Mes: {datetime.now().strftime('%B')}")
    cal = calendar.monthcalendar(datetime.now().year, datetime.now().month)
    cols = st.columns(7)
    for i, d in enumerate(['L','M','X','J','V','S','D']): cols[i].markdown(f"<div class='cal-header'>{d}</div>", unsafe_allow_html=True)
    
    df_journal['Fecha'] = pd.to_datetime(df_journal['Fecha'])
    m_data = df_journal[df_journal['Fecha'].dt.month == datetime.now().month]
    daily = m_data.groupby(m_data['Fecha'].dt.day)['PnL'].sum()
    
    for week in cal:
        cols = st.columns(7)
        for i, d in enumerate(week):
            if d!=0:
                pnl = daily.get(d, 0)
                cls = "win-day" if pnl>0 else "loss-day" if pnl<0 else ""
                txt = f"<span class='{'win-text' if pnl>0 else 'loss-text'}'>${pnl:,.0f}</span>" if pnl!=0 else "-"
                cols[i].markdown(f"<div class='pnl-cell {cls}'><div class='cell-date'>{d}</div><div class='cell-pnl'>{txt}</div></div>", unsafe_allow_html=True)
            else: cols[i].markdown("<div style='min-height:110px'></div>", unsafe_allow_html=True)

# ==============================================================================
# 6. CUENTAS (LOGICA COMPLETA)
# ==============================================================================
elif menu == "🏦 Cuentas":
    st.header("Gestión de Capital")
    tabs = st.tabs(["Activas", "Historial", "Grupos"])
    
    with tabs[0]:
        with st.expander("➕ Añadir Cuenta"):
            with st.form("new_acc"):
                c1, c2, c3 = st.columns(3)
                n = c1.text_input("Nombre")
                e = c2.text_input("Empresa")
                t = c3.selectbox("Tipo", ["Examen", "Funded"])
                c4, c5, c6 = st.columns(3)
                bi = c4.number_input("Balance Inicial", 50000.0)
                ba = c5.number_input("Balance Actual", 50000.0)
                bo = c6.number_input("Objetivo", 53000.0)
                c7, c8 = st.columns(2)
                do = c7.number_input("Días Winning", 5)
                co = c8.number_input("Coste ($)", 0.0)
                
                if st.form_submit_button("Crear"):
                    new = pd.DataFrame([{'Nombre': n, 'Empresa': e, 'Tipo': t, 'Balance_Inicial': bi, 'Balance_Actual': ba, 'Balance_Objetivo': bo, 'Dias_Objetivo': do, 'Costo': co, 'Estado': 'Activa', 'Fecha_Creacion': str(date.today())}])
                    df_accounts = pd.concat([df_accounts, new], ignore_index=True)
                    save_data(df_accounts, 'accounts')
                    if co > 0:
                        fin = pd.DataFrame([{'Fecha': str(date.today()), 'Tipo': 'GASTO', 'Concepto': f"Compra {n}", 'Monto': -abs(co)}])
                        df_finance = pd.concat([df_finance, fin], ignore_index=True); save_data(df_finance, 'finance')
                    st.success("Creada"); st.rerun()

        active = df_accounts[df_accounts['Estado']=='Activa']
        if active.empty: st.info("Sin cuentas activas")
        else:
            for i, r in active.iterrows():
                with st.container(border=True):
                    st.markdown(f"### 💳 {r['Nombre']} <small>({r['Tipo']})</small>", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    
                    # Logica Winning Days
                    wd = 0
                    pnl_j = 0
                    if not df_journal.empty:
                        acc_tr = df_journal[df_journal['Cuenta']==r['Nombre']]
                        if not acc_tr.empty:
                            pnl_j = acc_tr['PnL'].sum()
                            daily = acc_tr.groupby('Fecha')['PnL'].sum()
                            wd = daily[daily >= 150].count()
                    
                    c1.metric("Balance", f"${r['Balance_Actual']:,.2f}", f"PnL Journal: ${pnl_j:,.2f}")
                    c2.metric("Winning Days", f"{wd}/{int(r['Dias_Objetivo'])}")
                    
                    tgt = r['Balance_Objetivo'] - r['Balance_Inicial']
                    curr = r['Balance_Actual'] - r['Balance_Inicial']
                    pg = min(max(curr/tgt, 0.0), 1.0) if tgt!=0 else 0
                    c3.progress(pg, f"Meta: ${tgt:,.0f}")
                    
                    with st.expander("⚙️ Editar / Payout"):
                        with st.form(f"ed_{i}"):
                            nb = st.number_input("Nuevo Balance", value=float(r['Balance_Actual']))
                            act = st.selectbox("Acción", ["Guardar", "Pasar a Funded", "Archivar (Perdida)", "Archivar (Retirada)"])
                            if st.form_submit_button("Actualizar"):
                                df_accounts.at[i, 'Balance_Actual'] = nb
                                if "Funded" in act: df_accounts.at[i, 'Tipo'] = "Funded"
                                elif "Archivar" in act: df_accounts.at[i, 'Estado'] = "Historico"
                                save_data(df_accounts, 'accounts'); st.rerun()

    with tabs[1]:
        st.subheader("Historial")
        hist = df_accounts[df_accounts['Estado']!='Activa']
        if not hist.empty: st.dataframe(hist)
        else: st.info("Vacío")

    with tabs[2]:
        st.subheader("Grupos")
        with st.form("grp"):
            gn = st.text_input("Nombre Grupo")
            acs = st.multiselect("Cuentas", active['Nombre'].unique())
            if st.form_submit_button("Crear Grupo"):
                new = pd.DataFrame([{'Nombre_Grupo': gn, 'Cuentas': ",".join(acs)}])
                df_groups = pd.concat([df_groups, new], ignore_index=True)
                save_data(df_groups, 'groups'); st.success("Creado"); st.rerun()
        if not df_groups.empty: st.dataframe(df_groups)

# ==============================================================================
# 7. FINANZAS
# ==============================================================================
elif menu == "💰 Finanzas":
    st.header("Finanzas")
    st.info("💡 Edita las filas directamente para corregir.")
    edited = st.data_editor(df_finance, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Guardar Finanzas"):
        save_data(edited, 'finance'); st.success("Guardado"); st.rerun()
