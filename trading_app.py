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

# --- ESTILOS CSS (MEJORADOS PARA NO CORTAR LETRAS) ---
st.markdown("""
<style>
    /* Espaciado general */
    .block-container { padding-top: 2rem; padding-bottom: 5rem; }
    
    /* TARJETAS KPI */
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
    
    /* BARRAS PROGRESO */
    .stProgress > div > div > div > div { background-color: #00C076; }
    
    /* CALENDARIOS */
    .cal-header { font-weight: bold; text-align: center; padding: 10px; opacity: 0.8; text-transform: uppercase; }
    .pnl-cell, .calendar-day-agenda {
        min-height: 110px; border: 1px solid rgba(128, 128, 128, 0.2); margin: 4px;
        background-color: var(--secondary-background-color); padding: 8px; border-radius: 10px;
        display: flex; flex-direction: column; justify-content: space-between;
    }
    .cell-date { font-weight: bold; opacity: 0.6; font-size: 1em; }
    .cell-pnl { font-weight: 900; font-size: 1.4em; text-align: center; margin: auto; }
    
    /* Colores */
    .win-day { border-top: 4px solid #00C076; background-color: rgba(0, 192, 118, 0.05); }
    .loss-day { border-top: 4px solid #FF4D4D; background-color: rgba(255, 77, 77, 0.05); }
    .win-text { color: #00C076; } .loss-text { color: #FF4D4D; }
    
    /* Etiquetas */
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
                        new = pd.DataFrame([{'ID': 999, 'Tarea': '
