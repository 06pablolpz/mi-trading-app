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

# --- ESTILOS CSS MEJORADOS (FIX LETRA COMIDA) ---
st.markdown("""
<style>
    /* Ajuste global para dar aire al texto */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 5rem;
    }
    
    /* TARJETAS KPI */
    .kpi-card {
        background-color: var(--secondary-background-color);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        margin-bottom: 15px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        height: 100%;
    }
    
    .kpi-title {
        color: var(--text-color);
        opacity: 0.8;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        color: var(--text-color);
        line-height: 1.2;
    }
    
    /* BARRAS DE PROGRESO */
    .stProgress > div > div > div > div {
        background-color: #00C076;
    }
    
    /* CALENDARIOS */
    .cal-header {
        font-weight: bold;
        text-align: center;
        padding: 10px;
        color: var(--text-color);
        opacity: 0.9;
        font-size: 1em;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(128,128,128,0.1);
    }
    
    /* CELDAS DEL CALENDARIO */
    .calendar-day-agenda, .pnl-cell {
        min-height: 120px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin: 4px;
        background-color: var(--secondary-background-color);
        padding: 10px;
        border-radius: 10px;
        transition: transform 0.2s;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .calendar-day-agenda:hover, .pnl-cell:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        z-index: 2;
    }
    
    .cell-date {
        font-weight: bold;
        font-size: 1.1em;
        opacity: 0.6;
        margin-bottom: 5px;
    }
    
    /* Colores PnL */
    .win-day { border-top: 4px solid #00C076; background-color: rgba(0, 192, 118, 0.05); }
    .loss-day { border-top: 4px solid #FF4D4D; background-color: rgba(255, 77, 77, 0.05); }
    
    .cell-pnl {
        font-weight: 900;
        font-size: 1.6em;
        text-align: center;
        margin-top: auto;
        margin-bottom: auto;
    }
    
    .win-text { color: #00C076; }
    .loss-text { color: #FF4D4D; }
    
    /* ETIQUETAS EVENTOS */
    .event-tag {
        padding: 4px 8px;
        border-radius: 6px;
        margin-bottom: 4px;
        font-size: 11px;
        color: white;
        font-weight: 600;
        display: block;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .evt-payout { background-color: #00C076; }
    .evt-bill { background-color: #FF4D4D; }
    .evt-task { background-color: #3B8ED0; }

</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
SHEET_NAME = "Trading_Database"

@st.cache_resource
def get_connection():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = st.secrets["service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# --- GESTIÓN DE DATOS (CLOUD + CACHÉ) ---
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
        try:
            worksheet = sh.worksheet(TABS[key])
        except gspread.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=TABS[key], rows=100, cols=20)
            worksheet.append_row(COLS[key])
            return pd.DataFrame(columns=COLS[key])
            
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty: return pd.DataFrame(columns=COLS[key])
        
        # Convertir numéricos
        for col in df.columns:
            if col in ['PnL', 'RR', 'Monto', 'Balance_Inicial', 'Balance_Actual', 'Balance_Objetivo', 'Costo', 'Target_Dinero', 'Dias_Objetivo']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        return df
    except Exception as e:
        return pd.DataFrame(columns=COLS[key])

def save_data(df, key):
    client = get_connection()
    try:
        sh = client.open(SHEET_NAME)
        worksheet = sh.worksheet(TABS[key])
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando: {e}")

# Carga inicial
df_journal = load_data('journal')
df_accounts = load_data('accounts')
df_finance = load_data('finance')
df_objectives = load_data('objectives')
df_subs = load_data('subs')
df_groups = load_data('groups')

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
st.sidebar.caption(f"⚡ Conectado: {SHEET_NAME}")
if st.sidebar.button("🔄 Sincronizar Ahora"):
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.radio("Navegación", ["📊 Dashboard", "🎯 Agenda", "🧠 Insights", "✅ Checklist", "📓 Diario (Multi)", "🏦 Cuentas", "💰 Finanzas"])

# ==============================================================================
# 📊 TAB 1: DASHBOARD
# ==============================================================================
if menu == "📊 Dashboard":
    st.header("Visión General")
    target = 10000.0
    if not df_objectives.empty:
        meta = df_objectives[df_objectives['Tipo'] == 'META_ANUAL']
        if not meta.empty: target = float(meta.iloc[0]['Target_Dinero'])
    
    payouts = 0.0
    if not df_finance.empty:
        p_df = df_finance[df_finance['Tipo'].astype(str).str.contains("INGRESO", na=False)]
        payouts = p_df['Monto'].sum()
        
    prog = min(max(payouts/target, 0.0), 1.0)
    
    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        c1.subheader(f"🎯 Meta Payouts: ${target:,.0f}")
        c1.progress(prog)
        c1.caption(f"💰 Llevas retirados: **${payouts:,.2f}**")
        
        with c2:
            if st.button("Editar Meta"):
                with st.form("meta_f"):
                    nm = st.number_input("Nuevo Objetivo", value=target)
                    if st.form_submit_button("Guardar"):
                        df_objectives = df_objectives[df_objectives['Tipo'] != 'META_ANUAL']
                        new = pd.DataFrame([{'ID': 999, 'Tarea': 'Meta', 'Tipo': 'META_ANUAL', 'Fecha_Limite': str(date.today()), 'Estado': 'Active', 'Target_Dinero': nm}])
                        df_objectives = pd.concat([df_objectives, new], ignore_index=True)
                        save_data(df_objectives, 'objectives'); st.rerun()

    st.markdown("---")
    if not df_journal.empty:
        pnl = df_journal['PnL'].sum()
        wins = len(df_journal[df_journal['Resultado']=='WIN'])
        wr = (wins/len(df_journal)*100) if len(df_journal)>0 else 0
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("PnL Operativo", pnl, "currency")
        with c2: kpi_card("Win Rate", wr, "percent")
        with c3: kpi_card("Trades", len(df_journal), "number", False)
        with c4: kpi_card("Avg RR", df_journal['RR'].mean(), "number", False)
        
        st.subheader("Curva de Rendimiento")
        df_journal['Fecha'] = pd.to_datetime(df_journal['Fecha'])
        daily = df_journal.groupby('Fecha')['PnL'].sum().reset_index()
        fig = px.area(daily, x='Fecha', y='PnL', template="plotly_dark")
        fig.update_traces(line_color='#00C076', fillcolor='rgba(0, 192, 118, 0.1)')
        st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# 🎯 TAB 2: AGENDA
# ==============================================================================
elif menu == "🎯 Agenda":
    st.header("Agenda & Objetivos")
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("obj"):
            task = st.text_input("Nueva Tarea")
            if st.form_submit_button("Añadir"):
                new = pd.DataFrame([{'ID': len(df_objectives)+1, 'Tarea': task, 'Tipo': 'Diario', 'Fecha_Limite': str(date.today()), 'Estado': 'Pendiente', 'Target_Dinero': 0}])
                df_objectives = pd.concat([df_objectives, new], ignore_index=True)
                save_data(df_objectives, 'objectives'); st.rerun()
        
        st.subheader("Pendientes")
        tasks = df_objectives[(df_objectives['Tipo'] != 'META_ANUAL') & (df_objectives['Estado'] != 'Hecho')]
        if not tasks.empty:
            for i, row in tasks.iterrows():
                if st.checkbox(f"⬜ {row['Tarea']}", key=f"t_{i}"):
                    df_objectives.at[i, 'Estado'] = 'Hecho'
                    save_data(df_objectives, 'objectives'); st.rerun()
        else:
            st.info("Todo al día.")

    with c2:
        st.subheader("Calendario Mensual")
        cal = calendar.monthcalendar(datetime.now().year, datetime.now().month)
        cols = st.columns(7)
        dias = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']
        for i, c in enumerate(cols): c.markdown(f"<div class='cal-header'>{dias[i]}</div>", unsafe_allow_html=True)
        
        for week in cal:
            cols = st.columns(7)
            for i, d in enumerate(week):
                with cols[idx := i]:
                    if d != 0:
                        st.markdown(f"""<div class='calendar-day-agenda'><div class='cell-date'>{d}</div></div>""", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='min-height:120px'></div>", unsafe_allow_html=True)

# ==============================================================================
# 🧠 TAB 3: INSIGHTS
# ==============================================================================
elif menu == "🧠 Insights":
    st.header("Analítica Avanzada")
    if df_journal.empty:
        st.warning("Registra trades para ver datos.")
    else:
        df = df_journal.copy()
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df['Dia'] = df['Fecha'].dt.day_name()
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("PnL por Día")
            fig1 = px.bar(df.groupby('Dia')['PnL'].sum().reset_index(), x='Dia', y='PnL', color='PnL', color_continuous_scale=['#FF4D4D', '#00C076'])
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            st.subheader("Por Estrategia")
            fig2 = px.box(df, x='Estrategia', y='PnL', points="all")
            st.plotly_chart(fig2, use_container_width=True)

# ==============================================================================
# ✅ TAB 4: CHECKLIST
# ==============================================================================
elif menu == "✅ Checklist":
    st.header("Sala de Ejecución")
    col1, col2 = st.columns(2)
    with col1:
        strat = st.selectbox("Estrategia", ["RANGOS", "CANALES ANCHOS", "CANALES ESTRECHOS"])
    
    with st.container(border=True):
        ok = False
        if strat == "RANGOS":
            if st.checkbox("1. ¿Mínimo 3 patas/extremos?") and st.checkbox("2. ¿Entrada en extremo?") and st.checkbox("3. ¿Patrón H2/L2 claro?"): ok = True
        elif strat == "CANALES ANCHOS":
            if st.checkbox("1. ¿A favor de tendencia?") and st.checkbox("2. ¿Pullback profundo?") and st.checkbox("3. ¿Stop protegido?"): ok = True
        elif strat == "CANALES ESTRECHOS":
            if st.checkbox("1. ¿Retroceso 50%?") and st.checkbox("2. ¿Pullback corto?") and st.checkbox("3. ¿Sin rechazo fuerte?"): ok = True
        
        if ok: st.balloons(); st.success("✅ SETUP VÁLIDO - ¡DISPARA!")

# ==============================================================================
# 📓 TAB 5: DIARIO
# ==============================================================================
elif menu == "📓 Diario (Multi)":
    st.header("Diario de Operaciones")
    with st.expander("➕ NUEVO TRADE", expanded=True):
        mode = st.radio("Modo:", ["Cuenta Única", "Grupo Cuentas"], horizontal=True)
        with st.form("add_trade"):
            c1, c2 = st.columns(2)
            d = c1.date_input("Fecha")
            
            targets = []
            if mode == "Cuenta Única":
                accs = df_accounts[df_accounts['Estado']=='Activa']['Nombre'].unique()
                sel = c2.selectbox("Cuenta", accs if len(accs)>0 else ["General"])
                targets = [sel]
            else:
                grps = df_groups['Nombre_Grupo'].unique()
                sel_g = c2.selectbox("Grupo", grps if len(grps)>0 else [])
                if len(grps)>0:
                    targets = df_groups[df_groups['Nombre_Grupo']==sel_g]['Cuentas'].values[0].split(',')

            c3, c4, c5 = st.columns(3)
            pnl = c3.number_input("PnL ($)", step=10.0)
            res = c4.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            strat = c5.selectbox("Estrategia", ["RANGOS", "CANALES", "OTRO"])
            
            if st.form_submit_button("💾 Guardar Trade"):
                rows = []
                for t in targets:
                    rows.append({
                        'Fecha': str(d), 'Cuenta': t.strip(), 'Activo': 'NQ', 'Estrategia': strat,
                        'Resultado': res, 'RR': 0, 'PnL': pnl, 'Emociones': '', 'Screenshot': '', 'Notas': ''
                    })
                df_new = pd.DataFrame(rows)
                df_journal = pd.concat([df_journal, df_new], ignore_index=True)
                save_data(df_journal, 'journal')
                st.success("Trade guardado en la nube ☁️")
                st.rerun()

    # VISOR PnL CALENDAR
    st.subheader(f"Vista Mensual: {datetime.now().strftime('%B')}")
    cal = calendar.monthcalendar(datetime.now().year, datetime.now().month)
    cols = st.columns(7)
    dias = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']
    for i, c in enumerate(cols): c.markdown(f"<div class='cal-header'>{dias[i]}</div>", unsafe_allow_html=True)
    
    # Preparar datos mes
    df_journal['Fecha'] = pd.to_datetime(df_journal['Fecha'])
    month_data = df_journal[df_journal['Fecha'].dt.month == datetime.now().month]
    daily_pnl = month_data.groupby(month_data['Fecha'].dt.day)['PnL'].sum()
    
    for week in cal:
        cols = st.columns(7)
        for i, d in enumerate(week):
            with cols[i]:
                if d != 0:
                    pnl = daily_pnl.get(d, 0)
                    style = "win-day" if pnl > 0 else "loss-day" if pnl < 0 else ""
                    pnl_txt = f"<span class='{'win-text' if pnl>0 else 'loss-text'}'>${pnl:,.0f}</span>" if pnl != 0 else "-"
                    
                    st.markdown(f"""
                    <div class='pnl-cell {style}'>
                        <div class='cell-date'>{d}</div>
                        <div class='cell-pnl'>{pnl_txt}</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='min-height:120px'></div>", unsafe_allow_html=True)

# ==============================================================================
# 🏦 TAB 6: CUENTAS (COMPLETO V11.1)
# ==============================================================================
elif menu == "🏦 Cuentas":
    st.header("Gestión de Capital")
    
    tabs_acc = st.tabs(["📋 Gestión Cuentas", "📜 Historial", "👥 Grupos"])
    
    with tabs_acc[0]:
        with st.expander("➕ Añadir Nueva Cuenta", expanded=False):
            with st.form("acc_f"):
                c1, c2, c3 = st.columns(3)
                n = c1.text_input("Nombre (ej. Apex 01)")
                e = c2.text_input("Empresa (ej. Topstep)")
                t = c3.selectbox("Tipo", ["Examen", "Funded"])
                c4, c5, c6 = st.columns(3)
                bi = c4.number_input("Balance Inicial", value=50000.0)
                ba = c5.number_input("Balance Actual", value=50000.0)
                bo = c6.number_input("Balance Objetivo", value=53000.0)
                c7, c8 = st.columns(2)
                do = c7.number_input("Días Winning Objetivo", value=5)
                cost = c8.number_input("Coste ($)", value=0.0)
                
                if st.form_submit_button("Crear Cuenta"):
                    new_acc = pd.DataFrame([{'Nombre': n, 'Empresa': e, 'Tipo': t, 'Balance_Inicial': bi, 'Balance_Actual': ba, 'Balance_Objetivo': bo, 'Dias_Objetivo': do, 'Costo': cost, 'Estado': 'Activa', 'Fecha_Creacion': str(date.today())}])
                    df_accounts = pd.concat([df_accounts, new_acc], ignore_index=True)
                    save_data(df_accounts, 'accounts')
                    if cost > 0:
                        new_exp = pd.DataFrame([{'Fecha': str(date.today()), 'Tipo': 'GASTO (Cuenta)', 'Concepto': f"Compra {n} ({e})", 'Monto': -abs(cost)}])
                        df_finance = pd.concat([df_finance, new_exp], ignore_index=True); save_data(df_finance, 'finance')
                    st.success(f"Cuenta {n} creada."); st.rerun()

        st.markdown("---")
        active_accounts = df_accounts[df_accounts['Estado'] == 'Activa']
        if active_accounts.empty: st.info("No tienes cuentas activas.")
        else:
            for index, row in active_accounts.iterrows():
                with st.container(border=True):
                    st.markdown(f"### 💳 {row['Nombre']} <span style='font-size:0.8em; opacity:0.6'>({row['Empresa']} - {row['Tipo']})</span>", unsafe_allow_html=True)
                    col_met1, col_met2, col_met3 = st.columns(3)
                    
                    # Logica PnL y Winning Days
                    pnl_journal = 0.0
                    winning_days = 0
                    if not df_journal.empty:
                        trades_acc = df_journal[df_journal['Cuenta'] == row['Nombre']]
                        if not trades_acc.empty:
                            pnl_journal = trades_acc['PnL'].sum()
                            daily_pnl = trades_acc.groupby('Fecha')['PnL'].sum()
                            winning_days = daily_pnl[daily_pnl >= 150].count()

                    col_met1.metric("Balance Actual", f"${row['Balance_Actual']:,.2f}", f"PnL Journal: ${pnl_journal:,.2f}")
                    col_met2.metric("Winning Days (+150$)", f"{winning_days}/{int(row['Dias_Objetivo'])}")
                    
                    target_money = row['Balance_Objetivo'] - row['Balance_Inicial']
                    current_money = row['Balance_Actual'] - row['Balance_Inicial']
                    prog_money = min(max(current_money / target_money, 0.0), 1.0) if target_money > 0 else 0
                    col_met3.progress(prog_money, f"Objetivo: ${current_money:,.0f} / ${target_money:,.0f}")

                    with st.expander("⚙️ Editar / Payout"):
                        with st.form(f"edit_{index}"):
                            c_e1, c_e2 = st.columns(2)
                            new_bal = c_e1.number_input("Editar Balance Actual", value=float(row['Balance_Actual']), step=100.0, key=f"bal_{index}")
                            action = c_e2.selectbox("Acción", ["Mantener Activa", "Pasar a Funded 🏆", "Archivar (Perdida) 💀", "Archivar (Retirada) 🏁"], key=f"act_{index}")
                            if st.form_submit_button("Actualizar"):
                                df_accounts.at[index, 'Balance_Actual'] = new_bal
                                if action == "Pasar a Funded 🏆": df_accounts.at[index, 'Tipo'] = "Funded"
                                elif "Archivar" in action: df_accounts.at[index, 'Estado'] = "Historico"
                                save_data(df_accounts, 'accounts'); st.rerun()

    with tabs_acc[1]:
        st.subheader("Cementerio y Hall de la Fama")
        history_accounts = df_accounts[df_accounts['Estado'] != 'Activa']
        if history_accounts.empty: st.info("No hay cuentas en el historial.")
        else:
            st.dataframe(history_accounts, use_container_width=True)

    with tabs_acc[2]:
        st.subheader("Crear Grupo de Réplica")
        with st.form("grp_form"):
            g_name = st.text_input("Nombre del Grupo")
            active_names = df_accounts[df_accounts['Estado'] == 'Activa']['Nombre'].unique()
            g_accs = st.multiselect("Selecciona Cuentas", active_names)
            if st.form_submit_button("Guardar Grupo"):
                if g_name and g_accs:
                    new_grp = pd.DataFrame([{'Nombre_Grupo': g_name, 'Cuentas': ",".join(g_accs)}])
                    df_groups = pd.concat([df_groups, new_grp], ignore_index=True)
                    save_data(df_groups, 'groups'); st.success("Grupo creado."); st.rerun()
        if not df_groups.empty: st.dataframe(df_groups, use_container_width=True)

# ==============================================================================
# 💰 TAB 7: FINANZAS
# ==============================================================================
elif menu == "💰 Finanzas":
    st.header("Control Financiero")
    
    # Editor directo
    edited = st.data_editor(df_finance, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Guardar Cambios Finanzas"):
        save_data(edited, 'finance')
        st.success("Guardado en Google Drive")
        st.rerun()
