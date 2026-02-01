import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import calendar
import os
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Life & Trading OS Pro", layout="wide", page_icon="🧿")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .stApp { background-color: #F5F7F9; }
    .kpi-card {
        background-color: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
        margin-bottom: 10px; border: 1px solid #E0E0E0;
    }
    .kpi-title { color: #888; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { font-size: 24px; font-weight: 800; color: #333; }
    .stProgress > div > div > div > div { background-color: #00C076; }
    .cal-header { font-weight: bold; text-align: center; margin-bottom: 5px; color: #555; font-size: 0.9em; text-transform: uppercase; }
    .pnl-cell {
        height: 100px; border-radius: 12px; border: 1px solid #EAEAEA; margin: 4px; background: white;
        display: flex; flex-direction: column; justify-content: space-between; padding: 8px;
        transition: all 0.2s ease;
    }
    .pnl-cell:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); transform: translateY(-2px); }
    .cell-date { font-weight: bold; color: #888; font-size: 0.9em; }
    .cell-pnl { font-weight: 900; font-size: 1.4em; text-align: center; align-self: center; margin-bottom: 10px; }
    .win-day { background-color: #ECFDF5; border-color: #A7F3D0; }
    .loss-day { background-color: #FEF2F2; border-color: #FECACA; }
    .win-text { color: #047857; }
    .loss-text { color: #B91C1C; }
    .calendar-day-agenda { border: 1px solid #E0E0E0; background: white; height: 100px; padding: 5px; font-size: 12px; border-radius: 8px; margin: 2px; overflow-y: auto; }
    .event-tag { padding: 2px 5px; border-radius: 4px; margin-bottom: 2px; font-size: 10px; color: white; display: block; }
    .evt-payout { background-color: #00C076; } .evt-bill { background-color: #FF4D4D; } .evt-task { background-color: #3B8ED0; }
    div.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE ARCHIVOS ---
FILES = { 
    'journal': 'trading_journal_v5.csv', 
    'accounts': 'prop_firms_v2.csv',  # Cambiamos nombre por nueva estructura
    'finance': 'trading_finances.csv', 
    'objectives': 'objectives.csv', 
    'subs': 'subscriptions.csv',
    'groups': 'account_groups.csv'
}

def load_data(key, columns):
    if not os.path.exists(FILES[key]): return pd.DataFrame(columns=columns)
    df = pd.read_csv(FILES[key])
    if key == 'journal' and 'Screenshot' in df.columns:
        df['Screenshot'] = df['Screenshot'].fillna("").astype(str)
    return df

def save_data(df, key): df.to_csv(FILES[key], index=False)

# Cargar Datos (NUEVA ESTRUCTURA DE CUENTAS)
df_journal = load_data('journal', ['Fecha', 'Cuenta', 'Activo', 'Estrategia', 'Resultado', 'RR', 'PnL', 'Emociones', 'Screenshot', 'Notas'])
# Cuentas ahora tiene más campos
df_accounts = load_data('accounts', ['Nombre', 'Empresa', 'Tipo', 'Balance_Inicial', 'Balance_Actual', 'Balance_Objetivo', 'Dias_Objetivo', 'Costo', 'Estado', 'Fecha_Creacion'])
df_finance = load_data('finance', ['Fecha', 'Tipo', 'Concepto', 'Monto'])
df_objectives = load_data('objectives', ['ID', 'Tarea', 'Tipo', 'Fecha_Limite', 'Estado', 'Target_Dinero'])
df_subs = load_data('subs', ['Servicio', 'Monto', 'Dia_Renovacion'])
df_groups = load_data('groups', ['Nombre_Grupo', 'Cuentas'])

# --- SIDEBAR & BACKUP ---
st.sidebar.title("🧿 Life & Trading OS")

with st.sidebar.expander("💾 SEGURIDAD DATOS", expanded=False):
    csv_buffer = io.BytesIO()
    df_journal.to_csv(csv_buffer, index=False)
    st.download_button("Descargar Diario (CSV)", data=csv_buffer.getvalue(), file_name="backup_journal.csv", mime="text/csv")
    uploaded_file = st.file_uploader("Restaurar Diario", type=['csv'])
    if uploaded_file is not None and st.button("🚨 SOBRESCRIBIR"):
        df_restored = pd.read_csv(uploaded_file)
        save_data(df_restored, 'journal')
        st.success("Restaurado.")

menu = st.sidebar.radio("Navegación", ["📊 Dashboard & Meta", "🎯 Objetivos & Calendario", "🧠 Insights & Herramientas", "✅ Checklist Ejecución", "📓 Diario de Trades (Multi)", "🏦 Cuentas & Historial", "💰 Finanzas & ROI"])

# --- UTILS ---
def kpi_card(title, value, type="currency", color_logic=True):
    color = "black"
    if color_logic and isinstance(value, (int, float)): color = "#00C076" if value > 0 else "#FF4D4D" if value < 0 else "#F7B924"
    display = f"${value:,.2f}" if type == "currency" else f"{value:.1f}%" if type == "percent" else f"{value}"
    st.markdown(f"""<div class="kpi-card"><div class="kpi-title">{title}</div><div class="kpi-value" style="color:{color}">{display}</div></div>""", unsafe_allow_html=True)

# ==============================================================================
# 📊 TAB 1: DASHBOARD
# ==============================================================================
if menu == "📊 Dashboard & Meta":
    st.header("Visión General")
    financial_goal_row = df_objectives[df_objectives['Tipo'] == 'META_ANUAL']
    target_amount = float(financial_goal_row.iloc[0]['Target_Dinero']) if not financial_goal_row.empty else 10000.0
    
    total_payouts_real = 0.0
    if not df_finance.empty:
        payouts_df = df_finance[df_finance['Tipo'].str.contains("INGRESO", na=False)]
        total_payouts_real = payouts_df['Monto'].sum()
        
    progress_pct = min(max(total_payouts_real / target_amount, 0.0), 1.0)
    remaining = target_amount - total_payouts_real
    
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.subheader(f"🎯 Meta Anual (Payouts Reales): ${target_amount:,.0f}")
        c1.progress(progress_pct)
        if remaining > 0: c1.caption(f"💪 Has retirado **${total_payouts_real:,.2f}**. Faltan **${remaining:,.2f}** para tu objetivo.")
        else: c1.success(f"🎉 ¡OBJETIVO COMPLETADO! Retirado: ${total_payouts_real:,.2f}")
        with c2:
            new_target = st.number_input("Ajustar Meta ($)", value=target_amount, label_visibility="collapsed")
            if st.button("Actualizar"):
                df_objectives = df_objectives[df_objectives['Tipo'] != 'META_ANUAL']
                df_objectives = pd.concat([df_objectives, pd.DataFrame([{'ID': 999, 'Tarea': 'Meta', 'Tipo': 'META_ANUAL', 'Fecha_Limite': '2024-12-31', 'Estado': 'Active', 'Target_Dinero': new_target}])], ignore_index=True)
                save_data(df_objectives, 'objectives'); st.rerun()

    st.markdown("---")
    
    total_pnl_trading = df_journal['PnL'].sum()
    if not df_journal.empty:
        win_rate = (len(df_journal[df_journal['Resultado']=='WIN']) / len(df_journal) * 100)
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Trading P&L (Op.)", total_pnl_trading, "currency")
        with c2: kpi_card("Win Rate", win_rate, "percent")
        with c3: kpi_card("Total Trades", len(df_journal), "number", False)
        with c4: kpi_card("Avg. RR", df_journal['RR'].mean(), "number", False)
        
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            st.caption("Curva de Rendimiento (Operativo)")
            df_sorted = df_journal.sort_values('Fecha')
            df_sorted['Acum'] = df_sorted['PnL'].cumsum()
            fig = px.area(df_sorted, x='Fecha', y='Acum'); fig.update_traces(line_color='#00C076', fillcolor='rgba(0,192,118,0.1)')
            fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='white', plot_bgcolor='white', xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#eee'))
            st.plotly_chart(fig, use_container_width=True)
        with c_chart2:
            st.caption("Rendimiento Diario (Operativo)")
            daily = df_journal.groupby('Fecha')['PnL'].sum().reset_index()
            daily['Color'] = daily['PnL'].apply(lambda x: '#00C076' if x>=0 else '#FF4D4D')
            fig_bar = go.Figure([go.Bar(x=daily['Fecha'], y=daily['PnL'], marker_color=daily['Color'])])
            fig_bar.update_layout(margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='white', plot_bgcolor='white', xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#eee'))
            st.plotly_chart(fig_bar, use_container_width=True)

# ==============================================================================
# 🎯 TAB 2: OBJETIVOS & AGENDA
# ==============================================================================
elif menu == "🎯 Objetivos & Calendario":
    st.header("Planificación & Agenda")
    tabs = st.tabs(["📝 Checklist Objetivos", "📅 Agenda Mensual"])
    with tabs[0]:
        c_add, c_list = st.columns([1, 2])
        with c_add:
            with st.container(border=True):
                st.subheader("Nuevo Objetivo")
                with st.form("obj_form"):
                    task = st.text_input("Tarea")
                    tipo = st.selectbox("Frecuencia", ["Diario", "Semanal", "Mensual", "Puntual"])
                    deadline = st.date_input("Fecha Límite", date.today())
                    if st.form_submit_button("Añadir"):
                        df_objectives = pd.concat([df_objectives, pd.DataFrame([{'ID': len(df_objectives)+1, 'Tarea': task, 'Tipo': tipo, 'Fecha_Limite': deadline, 'Estado': 'Pendiente', 'Target_Dinero': 0}])], ignore_index=True)
                        save_data(df_objectives, 'objectives'); st.rerun()
        with c_list:
            st.subheader("Mis Tareas")
            tasks_view = df_objectives[df_objectives['Tipo'] != 'META_ANUAL']
            if not tasks_view.empty:
                for t_type in tasks_view['Tipo'].unique():
                    with st.expander(f"📌 {t_type}", expanded=True):
                        for i, row in tasks_view[tasks_view['Tipo'] == t_type].iterrows():
                            done = st.checkbox(f"{row['Tarea']} ({row['Fecha_Limite']})", value=(row['Estado']=='Hecho'), key=f"t_{row['ID']}")
                            if (done and row['Estado']!='Hecho') or (not done and row['Estado']=='Hecho'):
                                df_objectives.loc[df_objectives['ID'] == row['ID'], 'Estado'] = 'Hecho' if done else 'Pendiente'
                                save_data(df_objectives, 'objectives'); st.rerun()
    with tabs[1]:
        st.subheader(f"Agenda: {datetime.now().strftime('%B %Y')}")
        year, month = datetime.now().year, datetime.now().month
        cal = calendar.monthcalendar(year, month)
        cols = st.columns(7)
        days_name = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']
        for idx, col in enumerate(cols): col.markdown(f"<div class='cal-header'>{days_name[idx]}</div>", unsafe_allow_html=True)
        for week in cal:
            cols = st.columns(7)
            for idx, day in enumerate(week):
                with cols[idx]:
                    if day == 0: st.markdown("<div class='calendar-day-agenda' style='background: #f9f9f9; border:none;'></div>", unsafe_allow_html=True)
                    else:
                        events_html = ""
                        current_date = date(year, month, day)
                        for _, sub in df_subs.iterrows():
                            if int(sub['Dia_Renovacion']) == day: events_html += f"<span class='event-tag evt-bill'>💸 {sub['Servicio']}</span>"
                        for _, obj in df_objectives.iterrows():
                            try:
                                if pd.to_datetime(obj['Fecha_Limite']).date() == current_date and obj['Estado'] != 'Hecho': events_html += f"<span class='event-tag evt-task'>📍 {obj['Tarea']}</span>"
                            except: pass
                        st.markdown(f"<div class='calendar-day-agenda'><strong>{day}</strong><br>{events_html}</div>", unsafe_allow_html=True)

# ==============================================================================
# 🧠 TAB 3: INSIGHTS
# ==============================================================================
elif menu == "🧠 Insights & Herramientas":
    st.header("Análisis Profundo y Utilidades")
    tabs = st.tabs(["📊 Analítica Avanzada (Insights)", "🧮 Calculadora de Riesgo"])
    with tabs[0]:
        if df_journal.empty: st.info("Necesitas registrar trades para ver analíticas.")
        else:
            df_ins = df_journal.copy()
            df_ins['Fecha'] = pd.to_datetime(df_ins['Fecha'])
            df_ins['Día Semana'] = df_ins['Fecha'].dt.day_name()
            dias_es = {'Monday':'Lunes', 'Tuesday':'Martes', 'Wednesday':'Miércoles', 'Thursday':'Jueves', 'Friday':'Viernes', 'Saturday':'Sábado', 'Sunday':'Domingo'}
            df_ins['Día Semana'] = df_ins['Día Semana'].map(dias_es)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("PnL por Día de la Semana")
                pnl_day = df_ins.groupby('Día Semana')['PnL'].sum().reindex(['Lunes','Martes','Miércoles','Jueves','Viernes']).reset_index()
                fig_day = px.bar(pnl_day, x='Día Semana', y='PnL', color='PnL', color_continuous_scale=['red', 'green'])
                st.plotly_chart(fig_day, use_container_width=True)
            with col2:
                st.subheader("PnL por Activo")
                pnl_asset = df_ins.groupby('Activo')['PnL'].sum().reset_index()
                fig_asset = px.bar(pnl_asset, x='Activo', y='PnL', color='PnL', color_continuous_scale=['red', 'green'])
                st.plotly_chart(fig_asset, use_container_width=True)
                
            col3, col4 = st.columns(2)
            with col3:
                st.subheader("Rendimiento por Estrategia")
                fig_strat = px.box(df_ins, x='Estrategia', y='PnL', points="all")
                st.plotly_chart(fig_strat, use_container_width=True)
            with col4:
                st.subheader("Ratio de Win/Loss")
                fig_pie = px.pie(df_ins, names='Resultado', values='RR', hole=0.4) 
                st.plotly_chart(fig_pie, use_container_width=True)
    with tabs[1]:
        st.subheader("Calculadora de Posición (Prop Firms)")
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            account_size = c1.number_input("Tamaño Cuenta", value=50000)
            risk_pct = c2.number_input("Riesgo %", value=1.0, step=0.1)
            stop_points = c3.number_input("Stop Loss (Puntos)", value=10.0)
            c4, c5 = st.columns(2)
            tick_value = c4.number_input("Valor por Punto (ej. NQ=$20, ES=$50)", value=20.0)
            risk_amount = account_size * (risk_pct / 100)
            if stop_points > 0 and tick_value > 0:
                contracts = risk_amount / (stop_points * tick_value)
                c5.metric("Contratos a usar", f"{contracts:.1f}", f"Riesgo: ${risk_amount:.0f}")
                st.info(f"💡 Si tu stop es de **{stop_points} puntos** y quieres perder máximo **${risk_amount:.0f}**, debes entrar con **{int(contracts)} contratos** (redondeado).")
            else:
                c5.write("Define Stop y Valor.")

# ==============================================================================
# ✅ TAB 4: CHECKLIST
# ==============================================================================
elif menu == "✅ Checklist Ejecución":
    st.header("⚡ Sala de Operaciones")
    c1, c2 = st.columns(2)
    acc = c1.selectbox("Cuenta/Grupo", df_accounts['Nombre'].unique()) if not df_accounts.empty else "Demo"
    strat = c2.selectbox("Estrategia", ["RANGOS", "CANALES ANCHOS", "CANALES ESTRECHOS"])
    with st.container(border=True):
        ready = False
        if strat == "RANGOS":
            if st.checkbox("1. Mínimo 3 patas") and st.checkbox("2. Entrada en extremo") and st.checkbox("3. H2/L2 claro"): ready=True
        elif strat == "CANALES ANCHOS":
            if st.checkbox("1. A favor de tendencia") and st.checkbox("2. Pullback profundo") and st.checkbox("3. SL protegido"): ready=True
        elif strat == "CANALES ESTRECHOS":
            if st.checkbox("1. Retroceso 50%") and st.checkbox("2. Pullback corto") and st.checkbox("3. Sin rechazo fuerte"): ready=True
        if ready: st.success(f"🚀 GO! {acc} - {strat} Validado")
        else: st.warning("Completa las reglas.")

# ==============================================================================
# 📓 TAB 5: DIARIO
# ==============================================================================
elif menu == "📓 Diario de Trades (Multi)":
    st.header("Diario de Trades")
    
    with st.expander("➕ Registrar Nuevo Trade (Soporte Multi-Cuenta)", expanded=False):
        mode = st.radio("Modo de Entrada:", ["Cuenta Única", "Grupo de Cuentas"], horizontal=True)
        with st.form("new_trade"):
            c1, c2, c3 = st.columns(3)
            d = c1.date_input("Fecha", date.today())
            selected_accounts = []
            if mode == "Cuenta Única":
                # Filtrar solo cuentas activas para el desplegable
                acc_list = df_accounts[df_accounts['Estado']=='Activa']['Nombre'].unique() if not df_accounts.empty else ["General"]
                acc_single = c2.selectbox("Cuenta", acc_list)
                selected_accounts = [acc_single]
            else:
                if df_groups.empty: c2.warning("No hay grupos creados.")
                else:
                    grp_name = c2.selectbox("Seleccionar Grupo", df_groups['Nombre_Grupo'].unique())
                    if grp_name: selected_accounts = df_groups[df_groups['Nombre_Grupo'] == grp_name]['Cuentas'].values[0].split(',')

            asst = c3.text_input("Activo", "NQ")
            c4, c5, c6 = st.columns(3)
            s = c4.selectbox("Estrategia", ["Rangos", "Canales Anchos", "Canales Estrechos"])
            res = c5.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            pn = c6.number_input("PnL por Cuenta ($)", step=10.0)
            c7, c8, c9 = st.columns(3)
            rr = c7.number_input("RR", 2.0)
            emo = c8.selectbox("Psicología", ["Disciplinado", "Miedo", "Venganza", "FOMO"])
            link = c9.text_input("Link Captura")
            
            if st.form_submit_button("Guardar Trade(s)"):
                if not selected_accounts: st.error("No hay cuentas seleccionadas.")
                else:
                    new_rows = []
                    for acc_name in selected_accounts:
                        new_rows.append({'Fecha': d, 'Cuenta': acc_name.strip(), 'Activo': asst, 'Estrategia': s, 'Resultado': res, 'RR': rr, 'PnL': pn, 'Emociones': emo, 'Screenshot': link, 'Notas': f"Grupo: {mode}"})
                    df_journal = pd.concat([df_journal, pd.DataFrame(new_rows)], ignore_index=True)
                    save_data(df_journal, 'journal'); st.success(f"✅ Trade replicado en {len(selected_accounts)} cuentas."); st.rerun()

    journal_tabs = st.tabs(["🗓️ Vista Calendario PnL", "📝 Vista Tabla Historial", "🖼️ Galería (Playbook)"])
    with journal_tabs[0]:
        st.subheader(f"Rendimiento: {datetime.now().strftime('%B %Y')}")
        today = date.today()
        df_journal['Fecha'] = pd.to_datetime(df_journal['Fecha']).dt.date
        df_this_month = df_journal[(pd.to_datetime(df_journal['Fecha']).dt.month == today.month) & (pd.to_datetime(df_journal['Fecha']).dt.year == today.year)]
        daily_pnl_map = df_this_month.groupby('Fecha')['PnL'].sum().to_dict()
        month_total = df_this_month['PnL'].sum()
        cal = calendar.monthcalendar(today.year, today.month)
        cols = st.columns(7)
        days_name = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']
        for idx, col in enumerate(cols): col.markdown(f"<div class='cal-header'>{days_name[idx]}</div>", unsafe_allow_html=True)
        for week in cal:
            cols = st.columns(7)
            for idx, day in enumerate(week):
                with cols[idx]:
                    if day == 0: st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
                    else:
                        current_date = date(today.year, today.month, day)
                        pnl = daily_pnl_map.get(current_date, 0)
                        cell_class = "pnl-cell"; text_class = ""; pnl_display = "-"
                        if pnl > 0: cell_class += " win-day"; text_class = "win-text"; pnl_display = f"+${pnl:,.0f}"
                        elif pnl < 0: cell_class += " loss-day"; text_class = "loss-text"; pnl_display = f"-${abs(pnl):,.0f}"
                        st.markdown(f"<div class='{cell_class}'><div class='cell-date'>{day}</div><div class='cell-pnl {text_class}'>{pnl_display}</div></div>", unsafe_allow_html=True)
        st.markdown("---")
        total_color = "#00C076" if month_total >= 0 else "#FF4D4D"
        st.markdown(f"<h3 style='text-align: center;'>Total Mes: <span style='color:{total_color}; font-size: 1.5em;'>${month_total:,.2f}</span></h3>", unsafe_allow_html=True)

    with journal_tabs[1]:
        st.info("💡 Edita directamente. Selecciona fila + Supr para borrar.")
        edited = st.data_editor(df_journal.sort_values('Fecha', ascending=False), num_rows="dynamic", key="editor_j", use_container_width=True, column_config={"Screenshot": st.column_config.LinkColumn("Ver Gráfico")})
        if st.button("💾 Guardar Cambios Tabla"): save_data(edited, 'journal'); st.success("Guardado.")
    with journal_tabs[2]:
        st.subheader("🏆 Salón de la Fama")
        wins_with_pics = df_journal[(df_journal['Resultado'] == 'WIN') & (df_journal['Screenshot'] != "")]
        if wins_with_pics.empty: st.info("Aún no tienes trades ganadores con link de captura.")
        else:
            for i, row in wins_with_pics.iterrows():
                with st.container(border=True):
                    col_img, col_info = st.columns([2, 1])
                    with col_info:
                        st.markdown(f"**{row['Fecha']}** | {row['Activo']}"); st.success(f"+${row['PnL']} ({row['Estrategia']})"); st.write(f"_{row['Notas']}_"); st.link_button("Ver Gráfico Completo", row['Screenshot'])

# ==============================================================================
# 🏦 TAB 6: CUENTAS Y GRUPOS (NUEVA LOGICA V9)
# ==============================================================================
elif menu == "🏦 Cuentas & Historial":
    st.header("Gestión de Capital")
    
    tabs_acc = st.tabs(["📋 Gestión Cuentas", "📜 Historial (Perdidas/Pasadas)", "👥 Grupos de Cuentas"])
    
    # --- SUB-TAB 1: GESTIÓN DE CUENTAS ACTIVAS ---
    with tabs_acc[0]:
        
        # FORMULARIO AÑADIR CUENTA (MEJORADO)
        with st.expander("➕ Añadir Nueva Cuenta", expanded=False):
            with st.form("acc_f"):
                c1, c2, c3 = st.columns(3)
                n = c1.text_input("Nombre (ej. Apex 01)")
                e = c2.text_input("Empresa (ej. Topstep)")
                t = c3.selectbox("Tipo", ["Examen", "Funded"])
                
                c4, c5, c6 = st.columns(3)
                bi = c4.number_input("Balance Inicial", value=50000.0)
                # El balance actual empieza igual al inicial por defecto
                bo = c5.number_input("Balance Objetivo", value=53000.0)
                do = c6.number_input("Días Winning Objetivo", value=5)
                
                cost = st.number_input("Coste de la prueba ($) [Opcional]", value=0.0)
                
                if st.form_submit_button("Crear Cuenta"):
                    # Crear cuenta
                    new_acc = pd.DataFrame([{
                        'Nombre': n, 'Empresa': e, 'Tipo': t, 
                        'Balance_Inicial': bi, 'Balance_Actual': bi, # Empieza igual
                        'Balance_Objetivo': bo, 'Dias_Objetivo': do, 
                        'Costo': cost, 'Estado': 'Activa', 
                        'Fecha_Creacion': date.today()
                    }])
                    df_accounts = pd.concat([df_accounts, new_acc], ignore_index=True)
                    save_data(df_accounts, 'accounts')
                    
                    # Si hay coste, añadir a finanzas automáticamente
                    if cost > 0:
                        new_exp = pd.DataFrame([{
                            'Fecha': date.today(), 'Tipo': 'GASTO (Cuenta)', 
                            'Concepto': f"Compra {n} ({e})", 'Monto': -abs(cost)
                        }])
                        df_finance = pd.concat([df_finance, new_exp], ignore_index=True)
                        save_data(df_finance, 'finance')
                        
                    st.success(f"Cuenta {n} creada y gasto registrado.")
                    st.rerun()

        st.markdown("---")
        
        # MOSTRAR CUENTAS ACTIVAS
        active_accounts = df_accounts[df_accounts['Estado'] == 'Activa']
        
        if active_accounts.empty:
            st.info("No tienes cuentas activas. Crea una arriba.")
        else:
            for index, row in active_accounts.iterrows():
                with st.container(border=True):
                    # CABECERA
                    st.markdown(f"### 💳 {row['Nombre']} <span style='font-size:0.8em; color:grey'>({row['Empresa']} - {row['Tipo']})</span>", unsafe_allow_html=True)
                    
                    # DATOS
                    col_met1, col_met2, col_met3 = st.columns(3)
                    
                    # 1. BALANCE ACTUAL (Editado por usuario)
                    # Calculamos el PnL acumulado en el journal para referencia visual, pero usamos el Balance Actual guardado
                    pnl_journal = df_journal[df_journal['Cuenta'] == row['Nombre']]['PnL'].sum()
                    
                    col_met1.metric("Balance Actual", f"${row['Balance_Actual']:,.2f}", f"PnL Journal: ${pnl_journal:,.2f}")
                    
                    # 2. PROGRESO WINNING DAYS (Calculado Auto)
                    # Filtramos trades de esta cuenta, agrupamos por fecha, sumamos PnL diario
                    if not df_journal.empty:
                        trades_acc = df_journal[df_journal['Cuenta'] == row['Nombre']]
                        if not trades_acc.empty:
                            daily_pnl = trades_acc.groupby('Fecha')['PnL'].sum()
                            winning_days = daily_pnl[daily_pnl >= 150].count() # Umbral $150
                        else:
                            winning_days = 0
                    else:
                        winning_days = 0
                        
                    col_met2.metric("Winning Days (+150$)", f"{winning_days}/{int(row['Dias_Objetivo'])}")
                    
                    # 3. PROGRESO DINERO
                    target_money = row['Balance_Objetivo'] - row['Balance_Inicial']
                    current_money = row['Balance_Actual'] - row['Balance_Inicial']
                    prog_money = min(max(current_money / target_money, 0.0), 1.0) if target_money > 0 else 0
                    col_met3.progress(prog_money, f"Objetivo Dinero: ${current_money:,.0f} / ${target_money:,.0f}")

                    # --- ZONA DE EDICIÓN Y ACCIONES ---
                    with st.expander("⚙️ Gestionar / Editar / Payout"):
                        with st.form(f"edit_{index}"):
                            c_e1, c_e2 = st.columns(2)
                            new_bal = c_e1.number_input("Editar Balance Actual", value=float(row['Balance_Actual']), step=100.0, key=f"bal_{index}")
                            action = c_e2.selectbox("Acción Estado", ["Mantener Activa", "Pasar a Funded 🏆", "Archivar (Perdida) 💀", "Archivar (Retirada) 🏁"], key=f"act_{index}")
                            
                            if st.form_submit_button("Actualizar Cuenta"):
                                # Actualizar Balance
                                df_accounts.at[index, 'Balance_Actual'] = new_bal
                                
                                # Cambio de Estado
                                if action == "Pasar a Funded 🏆":
                                    df_accounts.at[index, 'Tipo'] = "Funded"
                                    # Resetear balance inicial al nuevo si se quiere, o dejarlo. 
                                    st.success(f"¡Felicidades! {row['Nombre']} ahora es Funded.")
                                    
                                elif "Archivar" in action:
                                    df_accounts.at[index, 'Estado'] = "Historico"
                                    # Podríamos añadir una nota de por qué se archivó en el nombre o columna nueva
                                    status_note = "Perdida" if "Perdida" in action else "Retirada"
                                    st.warning(f"Cuenta movida al historial como {status_note}.")
                                
                                save_data(df_accounts, 'accounts')
                                st.rerun()

    # --- SUB-TAB 2: HISTORIAL ---
    with tabs_acc[1]:
        st.subheader("Cementerio y Hall de la Fama")
        history_accounts = df_accounts[df_accounts['Estado'] != 'Activa']
        if history_accounts.empty:
            st.info("No hay cuentas en el historial.")
        else:
            st.dataframe(history_accounts, use_container_width=True)
            if st.button("🗑️ Borrar Historial Definitivamente"):
                # Mantener solo activas
                df_accounts = df_accounts[df_accounts['Estado'] == 'Activa']
                save_data(df_accounts, 'accounts')
                st.rerun()

    # --- SUB-TAB 3: GRUPOS ---
    with tabs_acc[2]:
        st.subheader("Crear Grupo de Réplica")
        with st.form("grp_form"):
            g_name = st.text_input("Nombre del Grupo")
            # Solo mostrar cuentas activas para agrupar
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
elif menu == "💰 Finanzas & ROI":
    st.header("Centro Financiero")
    with st.expander("🔄 Gestionar Suscripciones Recurrentes", expanded=False):
        c1, c2 = st.columns([2, 1])
        with c1: st.dataframe(df_subs, use_container_width=True)
        with c2:
            with st.form("sub_form"):
                srv = st.text_input("Servicio"); mnt = st.number_input("Monto ($)", 0.0); dia = st.number_input("Día (1-31)", 1, 31, 1)
                if st.form_submit_button("Añadir"): df_subs = pd.concat([df_subs, pd.DataFrame([{'Servicio': srv, 'Monto': mnt, 'Dia_Renovacion': dia}])], ignore_index=True); save_data(df_subs, 'subs'); st.rerun()
    if st.button("⚡ Generar Gastos de Este Mes"):
        today = date.today(); count = 0
        for _, sub in df_subs.iterrows():
            exists = False
            for _, fin in df_finance.iterrows():
                fin_date = pd.to_datetime(fin['Fecha']).date()
                if fin_date.month == today.month and fin_date.year == today.year and fin['Concepto'] == sub['Servicio']: exists = True
            if not exists: df_finance = pd.concat([df_finance, pd.DataFrame([{'Fecha': today, 'Tipo': 'GASTO (Suscripción)', 'Concepto': sub['Servicio'], 'Monto': -abs(sub['Monto'])}])], ignore_index=True); count += 1
        save_data(df_finance, 'finance'); st.success(f"{count} gastos generados."); st.rerun()
    st.markdown("---"); col_l, col_r = st.columns([1, 2])
    with col_l:
        with st.form("fin_manual"):
            fd = st.date_input("Fecha", date.today()); ft = st.selectbox("Tipo", ["GASTO", "INGRESO (Payout)"]); fc = st.text_input("Concepto"); fa = st.number_input("Monto ($)", 0.0)
            if st.form_submit_button("Guardar"): amt = fa if "INGRESO" in ft else -abs(fa); df_finance = pd.concat([df_finance, pd.DataFrame([{'Fecha': fd, 'Tipo': ft, 'Concepto': fc, 'Monto': amt}])], ignore_index=True); save_data(df_finance, 'finance'); st.rerun()
    with col_r:
        if not df_finance.empty:
            income = df_finance[df_finance['Monto'] > 0]['Monto'].sum(); expenses = abs(df_finance[df_finance['Monto'] < 0]['Monto'].sum()); net_profit = income - expenses; roi = ((income - expenses) / expenses * 100) if expenses > 0 else 0
            k1, k2, k3 = st.columns(3); k1.metric("Invertido", f"${expenses:,.2f}"); k2.metric("Retirado", f"${income:,.2f}"); k3.metric("Beneficio Neto", f"${net_profit:,.2f}", delta=f"{roi:.1f}% ROI")
            st.dataframe(df_finance.sort_values('Fecha', ascending=False), use_container_width=True, height=200)
