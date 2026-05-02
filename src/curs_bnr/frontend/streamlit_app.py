import streamlit as st
import requests
import pandas as pd
import os
import streamlit.components.v1 as components

# Importam config pentru a gasi folderul reports
from curs_bnr.config import REPORTS_DIR

# Configurare pagina
st.set_page_config(page_title="Prognoza Curs GBP/RON", layout="wide", page_icon="📈")

API_URL = "http://localhost:8000/api"

def get_data(endpoint):
    try:
        response = requests.get(f"{API_URL}/{endpoint}", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None

# CSS pentru un design premium (glassmorphism & cards)
st.markdown("""
<style>
    /* Fundal si font general */
    .main {
        background-color: #f0f2f6;
    }
    
    /* Titlu Centrat */
    .centered-title {
        text-align: center;
        color: #1e3d59;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
        margin-bottom: 30px;
    }

    /* Carduri KPI */
    .kpi-container {
        display: flex;
        justify-content: space-around;
        gap: 20px;
        margin-bottom: 30px;
    }
    .kpi-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        text-align: center;
        flex: 1;
        transition: transform 0.3s ease;
        border: 1px solid #eef0f2;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        color: #17a2b8; /* Cyan/Teal */
        margin-top: 10px;
    }
    .kpi-label {
        font-size: 13px;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    /* Container Grafice */
    .chart-container {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #eef0f2;
    }
    
    /* Stiluri Tab-uri */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: white !important;
        border-bottom: 3px solid #17a2b8 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Navigare prin Tab-uri (Top Navigation)
tab1, tab2, tab3 = st.tabs(["🏠 Landing", "📊 Antrenare & Evaluare", "🧪 Optuna Studies"])

# --- TAB 1: LANDING ---
with tab1:
    st.markdown('<h1 class="centered-title">📈 Prognoza Curs Valutar BNR: GBP/RON</h1>', unsafe_allow_html=True)
    
    # KPI Data Fetch
    forecast_data = get_data("forecast/latest")
    
    # KPI Row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rmse = forecast_data.get("best_rmse") if forecast_data else None
        val = f"{rmse:.4f}" if rmse else "N/A"
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-label">🏆 RMSE (Best Model)</div>
                <div class="kpi-value">{val}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        status = forecast_data.get("forecast_status", "N/A") if forecast_data else "Deconectat"
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-label">🛰️ Status Sistem</div>
                <div class="kpi-value">{status}</div>
            </div>
        ''', unsafe_allow_html=True)
        
    with col3:
        winner = forecast_data.get("winner_model") if forecast_data else "N/A"
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-label">🧠 Model Câștigător</div>
                <div class="kpi-value" style="font-size: 20px;">{winner}</div>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Historical Chart
    with st.container():
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("🕰️ Evoluție Istorică Curs GBP/RON")
        rates_data = get_data("rates")
        if rates_data:
            df_rates = pd.DataFrame(rates_data)
            df_rates['date'] = pd.to_datetime(df_rates['date'])
            df_rates = df_rates.sort_values('date')
            st.line_chart(df_rates.set_index('date')['gbp_rate'], use_container_width=True)
        else:
            st.warning("Backend-ul FastAPI nu este accesibil pe portul 8000.")
        
        c1, c2, c3 = st.columns([1, 1, 1])
        if c2.button("🔄 Actualizează Date (Scraping)", use_container_width=True):
            requests.post(f"{API_URL}/scrape")
            st.toast("Cererea de scraping a fost trimisă.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: ANTRENARE ---
with tab2:
    st.markdown('<h1 class="centered-title">📊 Analiză Performanță și Prognoză</h1>', unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader("📋 Metrici Modele")
        metrics_data = get_data("metrics")
        if metrics_data:
            df_metrics = pd.DataFrame(metrics_data)
            st.dataframe(df_metrics, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        if st.button("🚀 Reantrenează Modele", use_container_width=True):
            try:
                res = requests.post(f"{API_URL}/train")
                if res.status_code == 200:
                    st.info(res.json().get("message"))
            except:
                st.error("Eroare la contactarea backend-ului.")

    with col_right:
        st.subheader("🎯 Prognoză Hold-Out")
        plot_path = REPORTS_DIR / "forecast_plot.html"
        if os.path.exists(plot_path):
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            try:
                with open(plot_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    components.html(html_content, height=600, scrolling=True)
            except Exception as e:
                st.error(f"Eroare: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Graficul forecast_plot.html lipsește.")

# --- TAB 3: OPTUNA ---
with tab3:
    st.markdown('<h1 class="centered-title">🧪 Optimizare Hiperparametri (Optuna)</h1>', unsafe_allow_html=True)
    
    st.warning("ℹ️ **Notă:** Dashboard-urile Optuna trebuie pornite manual din terminal înainte de a accesa butoanele de vizualizare.")
    
    optuna_links = get_data("optuna-links")
    if optuna_links:
        cols = st.columns(len(optuna_links))
        for idx, link in enumerate(optuna_links):
            with cols[idx]:
                with st.expander(f"📌 {link['model']}", expanded=True):
                    status = "✅ Disponibil" if link['exists'] else "❌ Lipsă"
                    st.write(f"**Status:** {status}")
                    
                    if link['exists']:
                        st.link_button("🌐 Open Dashboard", link['dashboard_url'], use_container_width=True)
                        st.markdown("**Comandă PowerShell:**")
                        db_filename = os.path.basename(link['db_path'])
                        rel_path = f"outputs/optuna_studies/{db_filename}"
                        st.code(f"python -c \"from optuna_dashboard import run_server; run_server('sqlite:///{rel_path}', port={link['port']})\"", language="powershell")
                    else:
                        st.info("Rulează optimizarea pentru a genera DB.")
    else:
        st.warning("Nu am putut prelua datele Optuna.")

# Sidebar discret pentru setari de sistem
with st.sidebar:
    st.image("https://www.bnr.ro/Images/logo-bnr-blue.png", width=150)
    st.markdown("---")
    st.write("### ⚙️ System Info")
    st.write(f"**API Status:** {'🟢 Online' if get_data('rates') else '🔴 Offline'}")
    st.write("**Currency:** GBP / RON")
    st.markdown("---")
    st.caption("Aplicație de prognoză valutară BNR v1.0")
