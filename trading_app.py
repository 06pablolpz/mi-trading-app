import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import calendar
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Life & Trading OS Pro", layout="wide", page_icon="🧿")

# --- ESTILOS CSS (ESTILO TICKTICK + TRADEZELLA CALENDAR) ---
st.markdown("""
<style>
    .stApp { background-color: #F5F7F9; }
    
    /* KPI CARDS */
    .kpi-card {
        background-color: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
        margin-bottom: 10px; border: 1px solid #E0E0E0;
    }
    .kpi-title { color: #888; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { font-size: 24px; font-weight: 800; color: #333; }
    
    /* PROGRESS BARS */
    .stProgress > div > div > div > div { background-color: #00C076; }
    
    /* CALENDAR STYLES (AGENDA & PNL) */
    .cal-header { font-weight: bold; text-align: center; margin-bottom: 5px; color: #555; font-size: 0.9em; text-transform: uppercase; }
    
    /* PNL CALENDAR SPECIFIC */
    .pnl-cell {
        height: 100px; border-radius: 12px; border: 1px solid #EAEAEA; margin: 4px; background: white;
        display: flex; flex-direction: column; justify-content: space-between; padding: 8px;
        transition: all 0.2s ease;
    }
    .pnl-cell:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); transform: translateY(-2px); }
    .cell-date { font-weight: bold; color: #888; font-size: 0.9em; }
    .cell-pnl { font-weight: 900; font-size: 1.4em; text-align: center; align-self: center; margin-bottom: 10px; }
    
    .win-day { background-color: #ECFDF5; border-color: #A7F3D0; } /* Verde suave Zella style */
    .loss-day { background-color: #FEF2F2; border-color: #FECACA; } /* Rojo suave Zella style */
    .win-text { color: #047857; }
    .loss-text { color: #B91C1C; }
    
    /* Event tags for Agenda Calendar */
    .calendar-day-agenda { border: 1px solid #E0E0E0; background: white; height: 100px; padding: 5px; font-size: 12px; border-radius: 8px; margin: 2px; overflow-y: auto; }
    .event-tag { padding: 2px 5px; border-radius: 4px; margin-bottom: 2px; font-size: 10px; color: white; display: block; }
    .evt-payout { background-color: #00C076; } .evt-bill { background-color: #FF4D4D; } .evt-task { background-color: #3B8ED0; }

    div.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE ARCHIVOS ---
FILES = { 'journal': 'trading_journal_v5.csv', 'accounts': 'prop_firms.csv', 'finance': 'trading_finances.csv', 'objectives': 'objectives.csv', 'subs': 'subscriptions.csv' }

def load_data(key, columns):
    if not os.path.exists(FILES[key]): return pd.DataFrame(columns=columns)
    return pd.read_csv(FILES[key])
def save_data(df, key): df.to_csv(FILES[key], index=False)

# Cargar Datos
df_journal = load_data('journal', ['Fecha', 'Cuenta', 'Activo', 'Estrategia', 'Resultado', 'RR', 'PnL', 'Emociones', 'Screenshot', 'Notas'])
df_accounts = load_data('accounts', ['Nombre', 'Empresa', 'Balance_Inicial', 'Objetivo_Mensual', 'Fecha_Payout'])
df_finance = load_data('finance', ['Fecha', 'Tipo', 'Concepto', 'Monto'])
df_objectives = load_data('objectives', ['ID', 'Tarea', 'Tipo', 'Fecha_Limite', 'Estado', 'Target_Dinero'])
df_subs = load_data('subs', ['Servicio', 'Monto', 'Dia_Renovacion'])

# --- SIDEBAR ---
st.sidebar.title("🧿 Life & Trading OS")
menu = st.sidebar.radio("Navegación", ["📊 Dashboard & Meta", "🎯 Objetivos & Calendario", "✅ Checklist Ejecución", "📓 Diario de Trades", "🏦 Cuentas Fondeo", "💰 Finanzas & ROI"])

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
    total_pnl = df_journal['PnL'].sum()
    progress_pct = min(max(total_pnl / target_amount, 0.0), 1.0)
    remaining = target_amount - total_pnl
    
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.subheader(f"🎯 Meta Anual: ${target_amount:,.0f}")
        c1.progress(progress_pct)
        if remaining > 0: c1.caption(f"💪 Faltan **${remaining:,.2f}** para tu objetivo.")
        else: c1.success("🎉 ¡OBJETIVO COMPLETADO!")
        with c2:
            new_target = st.number_input("Ajustar Meta ($)", value=target_amount, label_visibility="collapsed")
            if st.button("Actualizar"):
                df_objectives = df_objectives[df_objectives['Tipo'] != 'META_ANUAL']
                df_objectives = pd.concat([df_objectives, pd.DataFrame([{'ID': 999, 'Tarea': 'Meta', 'Tipo': 'META_ANUAL', 'Fecha_Limite': '2024-12-31', 'Estado': 'Active', 'Target_Dinero': new_target}])], ignore_index=True)
                save_data(df_objectives, 'objectives'); st.rerun()

    st.markdown("---")
    if not df_journal.empty:
        win_rate = (len(df_journal[df_journal['Resultado']=='WIN']) / len(df_journal) * 100)
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Net P&L", total_pnl, "currency")
        with c2: kpi_card("Win Rate", win_rate, "percent")
        with c3: kpi_card("Total Trades", len(df_journal), "number", False)
        with c4: kpi_card("Avg. RR", df_journal['RR'].mean(), "number", False)
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            df_sorted = df_journal.sort_values('Fecha')
            df_sorted['Acum'] = df_sorted['PnL'].cumsum()
            fig = px.area(df_sorted, x='Fecha', y='Acum'); fig.update_traces(line_color='#00C076', fillcolor='rgba(0,192,118,0.1)')
            fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='white', plot_bgcolor='white', xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#eee'))
            st.plotly_chart(fig, use_container_width=True)
        with c_chart2:
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
                        for _, acc in df_accounts.iterrows():
                            if pd.to_datetime(acc['Fecha_Payout']).date() == current_date: events_html += f"<span class='event-tag evt-payout'>💰 Payout {acc['Empresa']}</span>"
                        for _, sub in df_subs.iterrows():
                            if int(sub['Dia_Renovacion']) == day: events_html += f"<span class='event-tag evt-bill'>💸 {sub['Servicio']}</span>"
                        for _, obj in df_objectives.iterrows():
                            try:
                                if pd.to_datetime(obj['Fecha_Limite']).date() == current_date and obj['Estado'] != 'Hecho': events_html += f"<span class='event-tag evt-task'>📍 {obj['Tarea']}</span>"
                            except: pass
                        st.markdown(f"<div class='calendar-day-agenda'><strong>{day}</strong><br>{events_html}</div>", unsafe_allow_html=True)

# ==============================================================================
# ✅ TAB 3: CHECKLIST
# ==============================================================================
elif menu == "✅ Checklist Ejecución":
    st.header("⚡ Sala de Operaciones")
    c1, c2 = st.columns(2)
    acc = c1.selectbox("Cuenta", df_accounts['Nombre'].unique()) if not df_accounts.empty else "Demo"
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
# 📓 TAB 4: DIARIO (CON CALENDARIO PNL)
# ==============================================================================
elif menu == "📓 Diario de Trades":
    st.header("Diario de Trades")

    # --- FORMULARIO DE ENTRADA RÁPIDA ---
    with st.expander("➕ Registrar Nuevo Trade", expanded=False):
        with st.form("new_trade"):
            c1, c2, c3 = st.columns(3)
            d = c1.date_input("Fecha", date.today())
            a = c2.selectbox("Cuenta", df_accounts['Nombre'].unique()) if not df_accounts.empty else c2.text_input("Cuenta", "General")
            asst = c3.text_input("Activo", "NQ")
            c4, c5, c6 = st.columns(3)
            s = c4.selectbox("Estrategia", ["Rangos", "Canales Anchos", "Canales Estrechos"])
            res = c5.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            pn = c6.number_input("PnL ($)", step=10.0)
            c7, c8, c9 = st.columns(3)
            rr = c7.number_input("RR", 2.0)
            emo = c8.selectbox("Psicología", ["Disciplinado", "Miedo", "Venganza", "FOMO"])
            link = c9.text_input("Link Captura")
            if st.form_submit_button("Guardar Trade"):
                new = pd.DataFrame([{'Fecha': d, 'Cuenta': a, 'Activo': asst, 'Estrategia': s, 'Resultado': res, 'RR': rr, 'PnL': pn, 'Emociones': emo, 'Screenshot': link, 'Notas': ''}])
                df_journal = pd.concat([df_journal, new], ignore_index=True)
                save_data(df_journal, 'journal'); st.rerun()

    # --- PESTAÑAS DE VISTA ---
    journal_tabs = st.tabs(["🗓️ Vista Calendario PnL", "📝 Vista Tabla Historial"])

    # --- VISTA CALENDARIO PNL ---
    with journal_tabs[0]:
        st.subheader(f"Rendimiento: {datetime.now().strftime('%B %Y')}")
        
        # 1. Preparar Datos del Mes Actual
        today = date.today()
        df_journal['Fecha'] = pd.to_datetime(df_journal['Fecha']).dt.date
        df_this_month = df_journal[(pd.to_datetime(df_journal['Fecha']).dt.month == today.month) & (pd.to_datetime(df_journal['Fecha']).dt.year == today.year)]
        daily_pnl_map = df_this_month.groupby('Fecha')['PnL'].sum().to_dict()
        month_total = df_this_month['PnL'].sum()

        # 2. Dibujar Calendario
        cal = calendar.monthcalendar(today.year, today.month)
        cols = st.columns(7)
        days_name = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']
        for idx, col in enumerate(cols): col.markdown(f"<div class='cal-header'>{days_name[idx]}</div>", unsafe_allow_html=True)

        for week in cal:
            cols = st.columns(7)
            for idx, day in enumerate(week):
                with cols[idx]:
                    if day == 0:
                        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
                    else:
                        current_date = date(today.year, today.month, day)
                        pnl = daily_pnl_map.get(current_date, 0)
                        
                        # Determinar estilos según PnL
                        cell_class = "pnl-cell"
                        text_class = ""
                        pnl_display = "-"
                        
                        if pnl > 0:
                            cell_class += " win-day"
                            text_class = "win-text"
                            pnl_display = f"+${pnl:,.0f}"
                        elif pnl < 0:
                            cell_class += " loss-day"
                            text_class = "loss-text"
                            pnl_display = f"-${abs(pnl):,.0f}"
                        
                        # HTML de la celda
                        st.markdown(f"""
                        <div class='{cell_class}'>
                            <div class='cell-date'>{day}</div>
                            <div class='cell-pnl {text_class}'>{pnl_display}</div>
                        </div>
                        """, unsafe_allow_html=True)
        
        # 3. Total del Mes
        st.markdown("---")
        total_color = "#00C076" if month_total >= 0 else "#FF4D4D"
        st.markdown(f"<h3 style='text-align: center;'>Total Mes: <span style='color:{total_color}; font-size: 1.5em;'>${month_total:,.2f}</span></h3>", unsafe_allow_html=True)


    # --- VISTA TABLA ---
    with journal_tabs[1]:
        st.info("💡 Edita directamente. Selecciona fila + Supr para borrar.")
        edited = st.data_editor(df_journal.sort_values('Fecha', ascending=False), num_rows="dynamic", key="editor_j", use_container_width=True, column_config={"Screenshot": st.column_config.LinkColumn("Ver Gráfico")})
        if st.button("💾 Guardar Cambios Tabla"):
            save_data(edited, 'journal'); st.success("Guardado.")

# ==============================================================================
# 🏦 TAB 5 & 💰 TAB 6 (MANTENIDOS IGUAL)
# ==============================================================================
elif menu == "🏦 Cuentas Fondeo":
    # (Código de cuentas igual que V5.0)
    st.header("Gestión de Capital")
    with st.expander("Añadir Cuenta"):
        with st.form("acc_f"):
            n = st.text_input("Nombre"); e = st.text_input("Empresa"); b = st.number_input("Balance Inicial", 50000.0); g = st.number_input("Objetivo", 3000.0); p = st.date_input("Fecha Payout")
            if st.form_submit_button("Crear"): df_accounts = pd.concat([df_accounts, pd.DataFrame([{'Nombre': n, 'Empresa': e, 'Balance_Inicial': b, 'Objetivo_Mensual': g, 'Fecha_Payout': p}])], ignore_index=True); save_data(df_accounts, 'accounts'); st.rerun()
    for i, r in df_accounts.iterrows():
        pnl_acc = df_journal[df_journal['Cuenta']==r['Nombre']]['PnL'].sum(); days = (pd.to_datetime(r['Fecha_Payout']).date() - date.today()).days
        with st.container(border=True):
            c1, c2, c3 = st.columns(3); c1.metric(r['Nombre'], f"${r['Balance_Inicial']+pnl_acc:,.2f}", f"{pnl_acc:,.2f}"); prog = min(max(pnl_acc/r['Objetivo_Mensual'],0.0),1.0) if r['Objetivo_Mensual']>0 else 0; c2.progress(prog, f"Objetivo: {prog*100:.1f}%"); c3.metric("Días Payout", days, delta_color="off")

elif menu == "💰 Finanzas & ROI":
    # (Código de finanzas igual que V5.0)
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
