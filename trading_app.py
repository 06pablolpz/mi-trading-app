import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="TradeZella Clone", layout="wide", page_icon="⚡")

# --- ESTILOS CSS (ESTILO TRADEZELLA: TARJETAS BLANCAS, SOMBRAS) ---
st.markdown("""
<style>
    /* Fondo general gris muy claro para contraste */
    .stApp {
        background-color: #F5F7F9;
    }
    
    /* Estilo de las Tarjetas de Métricas */
    .kpi-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        margin-bottom: 10px;
        border: 1px solid #E0E0E0;
    }
    
    .kpi-title {
        color: #6c757d;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
    }
    
    /* Colores para valores */
    .val-green { color: #00C076; }
    .val-red { color: #FF4D4D; }
    .val-yellow { color: #F7B924; }
    .val-black { color: #212529; }

    /* Ajustes generales */
    div.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE DATOS ---
JOURNAL_FILE = 'trading_journal_v3.csv'
ACCOUNTS_FILE = 'prop_firms.csv'
FINANCE_FILE = 'trading_finances.csv'

def load_data(file, columns):
    if not os.path.exists(file):
        return pd.DataFrame(columns=columns)
    return pd.read_csv(file)

def save_data(df, file):
    df.to_csv(file, index=False)

# Cargar Dataframes
df_journal = load_data(JOURNAL_FILE, ['Fecha', 'Cuenta', 'Activo', 'Estrategia', 'Resultado', 'RR', 'PnL', 'Emociones', 'Screenshot', 'Notas'])
df_accounts = load_data(ACCOUNTS_FILE, ['Nombre', 'Empresa', 'Tamaño', 'Balance_Inicial', 'Objetivo_Mensual', 'Fecha_Payout'])
df_finance = load_data(FINANCE_FILE, ['Fecha', 'Tipo', 'Concepto', 'Monto'])

# --- SIDEBAR ---
st.sidebar.title("⚡ Trader OS")
menu = st.sidebar.radio("Menú", ["📊 Dashboard", "✅ Checklist", "📓 Diario de Trades", "🏦 Cuentas Fondeo", "💰 Finanzas (Gastos/Ingresos)"])

# --- FUNCIÓN AUXILIAR PARA TARJETAS KPI HTML ---
def kpi_card(title, value, type="currency", color_logic=True):
    color_class = "val-black"
    display_value = value
    
    if color_logic:
        if isinstance(value, (int, float)):
            if value > 0: color_class = "val-green"
            elif value < 0: color_class = "val-red"
            else: color_class = "val-yellow"
    
    if type == "currency":
        display_value = f"${value:,.2f}"
    elif type == "percent":
        display_value = f"{value:.1f}%"
    elif type == "number":
        display_value = f"{value}"
        
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value {color_class}">{display_value}</div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 📊 PESTAÑA 1: DASHBOARD (ESTILO TRADEZELLA)
# ==============================================================================
if menu == "📊 Dashboard":
    st.header("Resumen de Rendimiento")
    
    if df_journal.empty:
        st.info("Añade trades en el Diario para ver tus métricas.")
    else:
        # CÁLCULOS
        total_pnl = df_journal['PnL'].sum()
        win_count = len(df_journal[df_journal['Resultado'] == 'WIN'])
        total_trades = len(df_journal)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        avg_rr = df_journal['RR'].mean()
        
        # 1. TARJETAS DE MÉTRICAS (HTML CUSTOM)
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Net P&L", total_pnl, "currency")
        with c2: kpi_card("Win Rate", win_rate, "percent", color_logic=True) # Verde si > 0, pero lógica podría ser > 50
        with c3: kpi_card("Total Trades", total_trades, "number", color_logic=False)
        with c4: kpi_card("Avg RR", avg_rr, "number", color_logic=False)

        st.markdown("---")

        # 2. GRÁFICOS ESTILIZADOS
        c_chart1, c_chart2 = st.columns(2)
        
        with c_chart1:
            st.subheader("Curva de Equidad")
            df_journal['Fecha'] = pd.to_datetime(df_journal['Fecha'])
            df_sorted = df_journal.sort_values('Fecha')
            df_sorted['Acumulado'] = df_sorted['PnL'].cumsum()
            
            # Gráfico de Área con degradado (Estilo TradeZella)
            fig_equity = px.area(df_sorted, x='Fecha', y='Acumulado')
            fig_equity.update_traces(line_color='#00C076', fillcolor='rgba(0, 192, 118, 0.2)')
            fig_equity.update_layout(
                plot_bgcolor='white', 
                paper_bgcolor='white',
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#F0F0F0')
            )
            st.plotly_chart(fig_equity, use_container_width=True)
            
        with c_chart2:
            st.subheader("PnL Diario")
            daily_pnl = df_journal.groupby('Fecha')['PnL'].sum().reset_index()
            # Colores condicionales para las barras
            colors = ['#00C076' if x >= 0 else '#FF4D4D' for x in daily_pnl['PnL']]
            
            fig_bar = go.Figure(data=[go.Bar(
                x=daily_pnl['Fecha'],
                y=daily_pnl['PnL'],
                marker_color=colors,
                marker_line_width=0
            )])
            fig_bar.update_layout(
                plot_bgcolor='white', 
                paper_bgcolor='white',
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#F0F0F0')
            )
            st.plotly_chart(fig_bar, use_container_width=True)

# ==============================================================================
# ✅ PESTAÑA 2: CHECKLIST
# ==============================================================================
elif menu == "✅ Checklist":
    st.header("⚡ Ejecución Disciplinada")
    
    col1, col2 = st.columns(2)
    with col1:
        acc_names = df_accounts['Nombre'].unique() if not df_accounts.empty else ["Sin Cuenta"]
        st.selectbox("Cuenta Activa", acc_names)
    with col2:
        strategy = st.selectbox("Estrategia", ["RANGOS", "CANALES ANCHOS", "CANALES ESTRECHOS"])

    with st.container(border=True):
        st.subheader(f"Reglas: {strategy}")
        ready = False
        
        if strategy == "RANGOS":
            c1 = st.checkbox("1. Mínimo 3 patas (extremos)")
            c2 = st.checkbox("2. Entrada en extremo (NO CENTRADO)")
            c3 = st.checkbox("3. Patrón H2/L2 claro")
            if c1 and c2 and c3: ready = True
            
        elif strategy == "CANALES ANCHOS":
            c1 = st.checkbox("1. A favor de tendencia (Pata Larga)")
            c2 = st.checkbox("2. Pullback profundo (2-3 patas)")
            c3 = st.checkbox("3. Stop Loss protegido")
            if c1 and c2 and c3: ready = True
            
        elif strategy == "CANALES ESTRECHOS":
            c1 = st.checkbox("1. Retroceso al 50%")
            c2 = st.checkbox("2. Pullback corto (< 3 velas)")
            c3 = st.checkbox("3. Sin rechazo fuerte en contra")
            if c1 and c2 and c3: ready = True

        if ready:
            st.success("✅ SETUP VÁLIDO. ¡DISPARA!")
        else:
            st.warning("❌ Completa el checklist.")

# ==============================================================================
# 📓 PESTAÑA 3: DIARIO (CON RR Y LINK)
# ==============================================================================
elif menu == "📓 Diario de Trades":
    st.header("Diario de Operaciones")
    
    with st.expander("➕ REGISTRAR NUEVO TRADE", expanded=True):
        with st.form("entry_form"):
            c1, c2, c3, c4 = st.columns(4)
            date_in = c1.date_input("Fecha", date.today())
            acc_in = c2.selectbox("Cuenta", df_accounts['Nombre'].unique()) if not df_accounts.empty else c2.text_input("Cuenta")
            asset_in = c3.text_input("Activo (ej. NQ)")
            rr_in = c4.number_input("Ratio RR (ej. 2.5)", step=0.1)
            
            c5, c6, c7, c8 = st.columns(4)
            strat_in = c5.selectbox("Estrategia", ["Rangos", "Canales Anchos", "Canales Estrechos"])
            res_in = c6.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            pnl_in = c7.number_input("PnL ($)", step=50.0)
            emo_in = c8.selectbox("Psicología", ["🎯 Disciplinado", "😨 Miedo", "😡 Venganza", "🤪 Fomo", "😌 Confiado"])
            
            link_in = st.text_input("Link Screenshot (TradingView)")
            notes_in = st.text_area("Notas / Review")
            
            if st.form_submit_button("Guardar Trade"):
                new_row = pd.DataFrame({
                    'Fecha': [date_in], 'Cuenta': [acc_in], 'Activo': [asset_in], 'Estrategia': [strat_in],
                    'Resultado': [res_in], 'RR': [rr_in], 'PnL': [pnl_in], 'Emociones': [emo_in],
                    'Screenshot': [link_in], 'Notas': [notes_in]
                })
                df_journal = pd.concat([df_journal, new_row], ignore_index=True)
                save_data(df_journal, JOURNAL_FILE)
                st.success("Trade guardado.")
                st.rerun()

    st.markdown("### 📋 Historial Reciente")
    # Estilizamos el dataframe
    st.dataframe(
        df_journal.sort_values('Fecha', ascending=False), 
        use_container_width=True,
        column_config={
            "Screenshot": st.column_config.LinkColumn("Ver Gráfico"),
            "PnL": st.column_config.NumberColumn("PnL", format="$%.2f")
        }
    )

# ==============================================================================
# 🏦 PESTAÑA 4: CUENTAS DE FONDEO
# ==============================================================================
elif menu == "🏦 Cuentas Fondeo":
    st.header("Gestión de Pruebas y Cuentas")
    
    with st.expander("➕ AÑADIR CUENTA"):
        with st.form("acc_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Nombre (ej. Apex 01)")
            firm = c2.text_input("Empresa (ej. Topstep)")
            c3, c4 = st.columns(2)
            bal_ini = c3.number_input("Balance Inicial", value=50000.0)
            goal = c4.number_input("Objetivo ($)", value=3000.0)
            pay_date = st.date_input("Fecha Payout")
            
            if st.form_submit_button("Crear Cuenta"):
                new_acc = pd.DataFrame({
                    'Nombre': [name], 'Empresa': [firm], 'Tamaño': ['N/A'], 'Balance_Inicial': [bal_ini],
                    'Objetivo_Mensual': [goal], 'Fecha_Payout': [pay_date]
                })
                df_accounts = pd.concat([df_accounts, new_acc], ignore_index=True)
                save_data(df_accounts, ACCOUNTS_FILE)
                st.rerun()

    # Visualización de Tarjetas de Cuenta
    if not df_accounts.empty:
        st.subheader("Estado Actual")
        for i, row in df_accounts.iterrows():
            # PnL específico de esta cuenta
            acc_pnl = df_journal[df_journal['Cuenta'] == row['Nombre']]['PnL'].sum()
            current_bal = row['Balance_Inicial'] + acc_pnl
            
            with st.container(border=True):
                st.markdown(f"**{row['Nombre']}** | {row['Empresa']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Balance", f"${current_bal:,.2f}", delta=f"${acc_pnl:,.2f}")
                
                # Barra de objetivo
                if row['Objetivo_Mensual'] > 0:
                    progreso = min(max(acc_pnl / row['Objetivo_Mensual'], 0.0), 1.0)
                    c2.progress(progreso, text=f"Objetivo: {progreso*100:.1f}%")
                
                days = (pd.to_datetime(row['Fecha_Payout']).date() - date.today()).days
                c3.metric("Días Payout", f"{days} días")

# ==============================================================================
# 💰 PESTAÑA 5: FINANZAS (GASTOS Y PAYOUTS)
# ==============================================================================
elif menu == "💰 Finanzas (Gastos/Ingresos)":
    st.header("Contabilidad del Negocio")
    
    # 1. FORMULARIO
    with st.expander("💵 REGISTRAR MOVIMIENTO", expanded=True):
        with st.form("fin_form"):
            c1, c2, c3 = st.columns(3)
            f_date = c1.date_input("Fecha", date.today())
            f_type = c2.selectbox("Tipo", ["GASTO (Prop Firm)", "GASTO (Software/Data)", "INGRESO (Payout)"])
            f_concept = c3.text_input("Concepto (ej. Reset Apex, TradingView)")
            f_amount = st.number_input("Monto ($)", min_value=0.0)
            
            if st.form_submit_button("Registrar"):
                # Si es GASTO, lo guardamos negativo. Si es INGRESO, positivo.
                final_amount = f_amount if "INGRESO" in f_type else -f_amount
                new_fin = pd.DataFrame({
                    'Fecha': [f_date], 'Tipo': [f_type], 'Concepto': [f_concept], 'Monto': [final_amount]
                })
                df_finance = pd.concat([df_finance, new_fin], ignore_index=True)
                save_data(df_finance, FINANCE_FILE)
                st.success("Movimiento registrado.")
                st.rerun()

    # 2. RESUMEN FINANCIERO
    if not df_finance.empty:
        total_income = df_finance[df_finance['Monto'] > 0]['Monto'].sum()
        total_expenses = df_finance[df_finance['Monto'] < 0]['Monto'].sum()
        net_finance = total_income + total_expenses
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1: kpi_card("Total Ingresos (Payouts)", total_income, "currency")
        with c2: kpi_card("Total Gastos", total_expenses, "currency") # Saldrá rojo automático
        with c3: kpi_card("Beneficio Neto (Caja)", net_finance, "currency")
        
        st.subheader("Detalle de Movimientos")
        st.dataframe(df_finance.sort_values('Fecha', ascending=False), use_container_width=True)
