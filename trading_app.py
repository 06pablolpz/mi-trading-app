import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os

# --- CONFIGURACIÓN DE PÁGINA (ESTILO WIDE) ---
st.set_page_config(page_title="Trading Pro Dashboard", layout="wide", page_icon="📈")

# --- ESTILOS CSS PERSONALIZADOS (PARECIDO A LA FOTO) ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .stMetric {
        background-color: #0E1117; 
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE DATOS ---
JOURNAL_FILE = 'trading_journal_v2.csv'
ACCOUNTS_FILE = 'prop_firms.csv'

def load_data(file, columns):
    if not os.path.exists(file):
        return pd.DataFrame(columns=columns)
    return pd.read_csv(file)

def save_data(df, file):
    df.to_csv(file, index=False)

# Cargar Dataframes
df_journal = load_data(JOURNAL_FILE, ['Fecha', 'Cuenta', 'Activo', 'Estrategia', 'Resultado', 'PnL', 'Emociones', 'Screenshot', 'Notas'])
df_accounts = load_data(ACCOUNTS_FILE, ['Nombre', 'Empresa', 'Tamaño', 'Balance_Inicial', 'Objetivo_Mensual', 'Fecha_Payout'])

# --- SIDEBAR (NAVEGACIÓN) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2910/2910312.png", width=50)
st.sidebar.title("Trader OS")
menu = st.sidebar.radio("Navegación", ["📊 Dashboard", "✅ Checklist Ejecución", "📓 Diario de Trades", "🏦 Cuentas & Payouts"])

# ==============================================================================
# 📊 PESTAÑA 1: DASHBOARD (ESTILO PRO)
# ==============================================================================
if menu == "📊 Dashboard":
    st.title("Good Morning, Trader!")
    
    if df_journal.empty:
        st.info("Registra tu primer trade en el Diario para ver estadísticas.")
    else:
        # 1. KPIs PRINCIPALES (FILA SUPERIOR)
        total_pnl = df_journal['PnL'].sum()
        win_count = len(df_journal[df_journal['Resultado'] == 'WIN'])
        total_trades = len(df_journal)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        avg_win = df_journal[df_journal['Resultado'] == 'WIN']['PnL'].mean() if win_count > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Net P&L ($)", f"${total_pnl:,.2f}", delta_color="normal")
        col2.metric("Win Rate", f"{win_rate:.1f}%")
        col3.metric("Total Trades", total_trades)
        col4.metric("Avg. Win Trade", f"${avg_win:,.2f}")

        # 2. GRÁFICOS
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Curva de Equidad (Acumulada)")
            df_journal['Fecha'] = pd.to_datetime(df_journal['Fecha'])
            df_sorted = df_journal.sort_values('Fecha')
            df_sorted['Acumulado'] = df_sorted['PnL'].cumsum()
            
            fig_equity = px.area(df_sorted, x='Fecha', y='Acumulado', color_discrete_sequence=['#00CC96'])
            fig_equity.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_equity, use_container_width=True)
            
        with col_chart2:
            st.subheader("PnL Diario")
            # Agrupar por día
            daily_pnl = df_journal.groupby('Fecha')['PnL'].sum().reset_index()
            daily_pnl['Color'] = daily_pnl['PnL'].apply(lambda x: 'green' if x >= 0 else 'red')
            
            fig_bar = go.Figure(data=[go.Bar(
                x=daily_pnl['Fecha'],
                y=daily_pnl['PnL'],
                marker_color=daily_pnl['Color']
            )])
            fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)

        # 3. ESTADÍSTICAS POR CUENTA
        st.subheader("Rendimiento por Cuenta")
        if not df_journal.empty:
            pnl_by_account = df_journal.groupby('Cuenta')['PnL'].sum().reset_index()
            st.dataframe(pnl_by_account, use_container_width=True)

# ==============================================================================
# ✅ PESTAÑA 2: CHECKLIST (DINÁMICO)
# ==============================================================================
elif menu == "✅ Checklist Ejecución":
    st.header("⚡ Antes de Disparar")
    
    # Selector de Cuenta y Estrategia
    col1, col2 = st.columns(2)
    with col1:
        if not df_accounts.empty:
            account_select = st.selectbox("¿En qué cuenta vas a operar?", df_accounts['Nombre'].unique())
        else:
            st.warning("Ve a 'Cuentas' y crea una primero.")
            account_select = "Sin Cuenta"
            
    with col2:
        strategy = st.selectbox("Selecciona Estrategia", ["RANGOS", "CANALES ANCHOS", "CANALES ESTRECHOS"])

    st.divider()
    
    # LOGICA DEL CHECKLIST SEGUN ESTRATEGIA
    ready_to_trade = False
    
    if strategy == "RANGOS":
        st.subheader("🎯 Checklist: RANGOS")
        c1 = st.checkbox("1. ¿Tiene mínimo 3 patas (extremos)?")
        c2 = st.checkbox("2. ¿Entrada en extremo (NO CENTRADO)?")
        c3 = st.checkbox("3. ¿Patrón H2/L2 claro?")
        if c1 and c2 and c3:
            ready_to_trade = True

    elif strategy == "CANALES ANCHOS":
        st.subheader("🌊 Checklist: CANALES ANCHOS")
        c1 = st.checkbox("1. ¿A favor de tendencia (Pata Larga)?")
        c2 = st.checkbox("2. ¿Pullback de calidad (2-3 patas)?")
        c3 = st.checkbox("3. ¿Stop Loss protegido en pata anterior?")
        if c1 and c2 and c3:
            ready_to_trade = True

    elif strategy == "CANALES ESTRECHOS":
        st.subheader("🚀 Checklist: CANALES ESTRECHOS")
        c1 = st.checkbox("1. ¿Retroceso al 50%?")
        c2 = st.checkbox("2. ¿Pullback de 3 velas o menos?")
        c3 = st.checkbox("3. ¿NO hay velas fuertes en contra?")
        if c1 and c2 and c3:
            ready_to_trade = True
            
    # Resultado
    if ready_to_trade:
        st.success("✅ SETUP APROBADO. ¡EJECUTA EL PLAN!")
        # Muestra un resumen rápido de reglas de salida
        st.info("💡 RECUERDA: Gestión de salida según PDF (10 velas o estructura).")
    else:
        st.caption("Marca todas las casillas para validar el trade.")

# ==============================================================================
# 📓 PESTAÑA 3: DIARIO (CON FOTOS Y EMOCIONES)
# ==============================================================================
elif menu == "📓 Diario de Trades":
    st.header("Registro de Operaciones")
    
    with st.expander("➕ AÑADIR NUEVO TRADE", expanded=True):
        with st.form("entry_form"):
            c1, c2, c3 = st.columns(3)
            date_in = c1.date_input("Fecha", date.today())
            acc_in = c2.selectbox("Cuenta", df_accounts['Nombre'].unique()) if not df_accounts.empty else c2.text_input("Cuenta (Nombre)")
            asset_in = c3.text_input("Activo (ej. NQ)")
            
            c4, c5, c6 = st.columns(3)
            strat_in = c4.selectbox("Estrategia Usada", ["Rangos", "Canales Anchos", "Canales Estrechos", "Otra"])
            res_in = c5.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            pnl_in = c6.number_input("PnL ($)", step=50.0)
            
            c7, c8 = st.columns(2)
            emo_in = c7.selectbox("Emociones", ["Neutro/Disciplinado", "Ansioso/Fomo", "Venganza", "Miedo", "Euforia"])
            link_in = c8.text_input("Link Captura (TradingView/Lightshot)")
            
            notes_in = st.text_area("Notas Técnicas")
            
            submit = st.form_submit_button("💾 Guardar Trade")
            
            if submit:
                new_data = pd.DataFrame({
                    'Fecha': [date_in], 'Cuenta': [acc_in], 'Activo': [asset_in],
                    'Estrategia': [strat_in], 'Resultado': [res_in], 'PnL': [pnl_in],
                    'Emociones': [emo_in], 'Screenshot': [link_in], 'Notas': [notes_in]
                })
                df_journal = pd.concat([df_journal, new_data], ignore_index=True)
                save_data(df_journal, JOURNAL_FILE)
                st.success("Trade registrado.")
                st.rerun()

    st.subheader("Historial Reciente")
    # Mostrar tabla con columnas seleccionadas para que se vea limpio
    st.dataframe(df_journal.sort_values('Fecha', ascending=False), use_container_width=True)

# ==============================================================================
# 🏦 PESTAÑA 4: GESTIÓN DE CUENTAS (PROP FIRMS)
# ==============================================================================
elif menu == "🏦 Cuentas & Payouts":
    st.header("Gestión de Prop Firms")
    
    # Formulario para añadir cuenta
    with st.expander("➕ AÑADIR NUEVA CUENTA"):
        with st.form("account_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Nombre Identificativo (ej. Apex 1)")
            firm = c2.text_input("Empresa (ej. Topstep)")
            
            c3, c4 = st.columns(2)
            size = c3.selectbox("Tamaño Cuenta", ["25k", "50k", "100k", "150k", "300k"])
            bal_ini = c4.number_input("Balance Inicial", value=50000.0)
            
            c5, c6 = st.columns(2)
            goal = c5.number_input("Objetivo Mensual ($)", value=3000.0)
            pay_date = c6.date_input("Próximo Payout")
            
            sub_acc = st.form_submit_button("Crear Cuenta")
            
            if sub_acc:
                new_acc = pd.DataFrame({
                    'Nombre': [name], 'Empresa': [firm], 'Tamaño': [size],
                    'Balance_Inicial': [bal_ini], 'Objetivo_Mensual': [goal],
                    'Fecha_Payout': [pay_date]
                })
                df_accounts = pd.concat([df_accounts, new_acc], ignore_index=True)
                save_data(df_accounts, ACCOUNTS_FILE)
                st.success(f"Cuenta {name} creada.")
                st.rerun()

    st.divider()
    
    # VISUALIZACIÓN DE ESTADO DE CUENTAS
    if not df_accounts.empty:
        st.subheader("Estado de Cuentas")
        
        for index, row in df_accounts.iterrows():
            # Calcular PnL actual de esa cuenta leyendo del Journal
            pnl_cuenta = df_journal[df_journal['Cuenta'] == row['Nombre']]['PnL'].sum()
            balance_actual = row['Balance_Inicial'] + pnl_cuenta
            
            # Calcular días para payout
            dias_payout = (pd.to_datetime(row['Fecha_Payout']).date() - date.today()).days
            
            with st.container():
                # Diseño de tarjeta para cada cuenta
                st.markdown(f"### 💳 {row['Nombre']} ({row['Empresa']})")
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("Balance Actual", f"${balance_actual:,.2f}", delta=f"{pnl_cuenta:.2f}")
                col2.metric("Objetivo", f"${row['Objetivo_Mensual']:,.0f}")
                
                # Barra de progreso del objetivo
                progreso = min(max(pnl_cuenta / row['Objetivo_Mensual'], 0.0), 1.0) if row['Objetivo_Mensual'] > 0 else 0
                col3.progress(progreso, text=f"Progreso Objetivo: {progreso*100:.1f}%")
                
                color_dias = "off" if dias_payout > 7 else "normal" # Alerta si falta poco
                col4.metric("Días para Payout", f"{dias_payout} días", delta_color=color_dias)
                
                st.markdown("---")
    else:
        st.info("Añade tu primera cuenta de fondeo arriba.")
