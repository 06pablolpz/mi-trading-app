import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Trading Plan & Journal", layout="wide", page_icon="📈")

# --- GESTIÓN DE DATOS ---
JOURNAL_FILE = 'trading_journal.csv'
FINANCE_FILE = 'trading_finances.csv'

def load_data(file, columns):
    if not os.path.exists(file):
        return pd.DataFrame(columns=columns)
    return pd.read_csv(file)

def save_data(df, file):
    df.to_csv(file, index=False)

# Cargar datos
df_journal = load_data(JOURNAL_FILE, ['Fecha', 'Activo', 'Estrategia', 'Resultado', 'PnL', 'Notas'])
df_finance = load_data(FINANCE_FILE, ['Fecha', 'Tipo', 'Concepto', 'Monto'])

# --- BARRA LATERAL (REGLAS DIARIAS) ---
st.sidebar.header("🛡️ Gestión de Riesgo Diaria")
st.sidebar.markdown("---")

daily_loss = st.sidebar.number_input("Pérdida actual hoy ($)", min_value=0.0, value=0.0)
trading_hours = st.sidebar.number_input("Horas operando", min_value=0.0, value=0.0)

bloqueo = False
if daily_loss >= 500:
    st.sidebar.error("❌ STOP: Límite de pérdida ($500) alcanzado.")
    bloqueo = True
if trading_hours >= 3:
    st.sidebar.error("❌ STOP: Límite de tiempo (3h) alcanzado.")
    bloqueo = True

st.sidebar.markdown("---")
st.sidebar.info("Recuerda: Solo Trades A+")

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs(["🚦 Validador de Trade", "📖 Diario de Trades", "💰 Finanzas/Gastos", "📊 Dashboard"])

# --- TAB 1: VALIDADOR (CHECKLIST DEL PDF) ---
with tab1:
    st.header("Checklist de Ejecución")
    
    if bloqueo:
        st.error("⛔ NO PUEDES OPERAR HOY: Has violado tus reglas diarias.")
    else:
        scenario = st.selectbox("¿Qué escenario estás viendo?", 
                                ["Selecciona...", "RANGOS", "CANALES ANCHOS", "CANALES ESTRECHOS"])
        
        decision = False
        
        if scenario == "RANGOS":
            st.subheader("Reglas de Rango")
            c1 = st.checkbox("¿Tiene mínimo 3 patas (extremos)?")
            c2 = st.checkbox("¿Entrada en extremo (NO CENTRADO)?")
            c3 = st.checkbox("¿Patrón H2/L2 claro?")
            c4 = st.checkbox("¿Conteo de impulsos favorable?")
            
            if c1 and c2 and c3 and c4:
                st.success("✅ SETUP VÁLIDO: Busca 2:1. Salir si en 10 velas no rompe.")
                decision = True
            else:
                st.warning("Completa el checklist.")

        elif scenario == "CANALES ANCHOS":
            st.subheader("Reglas de Canales Anchos")
            c1 = st.checkbox("¿A favor de tendencia (Pata Larga)?")
            c2 = st.checkbox("¿Pullback de calidad (2-3 patas)?")
            c3 = st.checkbox("¿H2/L2 visible?")
            
            if c1 and c2 and c3:
                st.success("✅ SETUP VÁLIDO: Stop en pata anterior. Mover SL con nuevos mínimos/máximos.")
                decision = True
            else:
                st.warning("Completa el checklist.")

        elif scenario == "CANALES ESTRECHOS":
            st.subheader("Reglas de Canales Estrechos")
            c1 = st.checkbox("¿Retroceso al 50%?")
            c2 = st.checkbox("¿Pullback duró 3 velas o menos?")
            c3 = st.checkbox("NO hay 3 velas fuertes en contra")
            c4 = st.checkbox("NO hay rechazo con mecha grande")
            
            if c1 and c2 and c3 and c4:
                st.success("✅ SETUP VÁLIDO: Usar Limit Order. Buscar 1:1 al anterior máximo.")
                decision = True
            else:
                st.warning("Completa el checklist.")

        # Confirmación ICT (Auxiliar)
        if decision:
            st.markdown("---")
            st.write("🔍 **Confirmación Extra (ICT Concepts):**")
            ict = st.checkbox("¿Reacción en FVG o Zona de Liquidez?")
            if ict:
                st.success("💎 TRADE A+ CONFIRMADO")

# --- TAB 2: DIARIO DE TRADES ---
with tab2:
    st.header("Registrar Nuevo Trade")
    with st.form("journal_form"):
        col1, col2 = st.columns(2)
        date_trade = col1.date_input("Fecha", datetime.today())
        asset = col2.text_input("Activo (ej. NQ, ES, EURUSD)")
        strat = st.selectbox("Estrategia", ["Rangos", "Canales Anchos", "Canales Estrechos", "Otro"])
        result = st.selectbox("Resultado", ["WIN", "LOSS", "BE"])
        pnl = st.number_input("PnL ($)", step=10.0)
        notes = st.text_area("Notas / Errores / Emociones")
        
        submitted = st.form_submit_button("Guardar Trade")
        
        if submitted:
            new_trade = pd.DataFrame({
                'Fecha': [date_trade], 'Activo': [asset], 'Estrategia': [strat], 
                'Resultado': [result], 'PnL': [pnl], 'Notas': [notes]
            })
            df_journal = pd.concat([df_journal, new_trade], ignore_index=True)
            save_data(df_journal, JOURNAL_FILE)
            st.success("Trade guardado correctamente.")

    st.subheader("Histórico Reciente")
    st.dataframe(df_journal.tail(10))

# --- TAB 3: FINANZAS ---
with tab3:
    st.header("Control de Gastos y Payouts")
    with st.form("finance_form"):
        col1, col2 = st.columns(2)
        f_date = col1.date_input("Fecha", datetime.today())
        f_type = col2.selectbox("Tipo", ["Gasto - Prop Firm", "Gasto - Software", "Gasto - Educación", "INGRESO - Payout"])
        f_concept = st.text_input("Concepto (ej. Prueba Apex, TradingView Pro)")
        f_amount = st.number_input("Monto ($)", min_value=0.0, step=10.0)
        
        # Ajustar signo según tipo
        submitted_fin = st.form_submit_button("Registrar Movimiento")
        
        if submitted_fin:
            final_amount = f_amount if "INGRESO" in f_type else -f_amount
            new_fin = pd.DataFrame({
                'Fecha': [f_date], 'Tipo': [f_type], 'Concepto': [f_concept], 'Monto': [final_amount]
            })
            df_finance = pd.concat([df_finance, new_fin], ignore_index=True)
            save_data(df_finance, FINANCE_FILE)
            st.success("Movimiento financiero guardado.")

    st.subheader("Movimientos")
    st.dataframe(df_finance)

# --- TAB 4: DASHBOARD ---
with tab4:
    st.header("Estadísticas Generales")
    
    if not df_journal.empty:
        # Métricas principales
        total_pnl_trades = df_journal['PnL'].sum()
        total_payouts_fees = df_finance['Monto'].sum() if not df_finance.empty else 0
        net_profit = total_pnl_trades + total_payouts_fees # Ojo: PnL trades es hipotético si es cuenta de fondeo, ajustar según realidad
        
        col1, col2, col3 = st.columns(3)
        col1.metric("PnL Bruto (Trades)", f"${total_pnl_trades:,.2f}")
        col2.metric("Balance Financiero (Caja)", f"${total_payouts_fees:,.2f}")
        col3.metric("Win Rate", f"{(len(df_journal[df_journal['Resultado']=='WIN']) / len(df_journal) * 100):.1f}%")

        # Gráfica de PnL Acumulado (Trades)
        st.subheader("Curva de Rendimiento (Trades)")
        df_journal['PnL_Acum'] = df_journal['PnL'].cumsum()
        st.line_chart(df_journal['PnL_Acum'])
        
        # Distribución de Estrategias
        st.subheader("Rendimiento por Estrategia")
        st.bar_chart(df_journal.groupby('Estrategia')['PnL'].sum())

    else:
        st.info("Añade trades para ver tus estadísticas.")
