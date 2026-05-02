import streamlit as st
import requests
import pandas as pd
import os
import streamlit.components.v1 as components

# Importam config pentru a gasi folderul reports
from curs_bnr.config import REPORTS_DIR

# Configurare pagina
st.set_page_config(page_title="Prognoza Curs GBP/RON", layout="wide")

API_URL = "http://localhost:8000/api"

def get_data(endpoint):
    try:
        response = requests.get(f"{API_URL}/{endpoint}", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None

# Sidebar
st.sidebar.title("Navigare")
tab_selection = st.sidebar.radio("Selecteaza Tab", ["Landing", "Antrenare", "Optuna"])

# CSS pentru carduri KPI elegante
st.markdown("""
<style>
.kpi-card {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
    border: 1px solid #dee2e6;
}
.kpi-value {
    font-size: 20px;
    font-weight: bold;
    color: #2c3e50;
}
.kpi-label {
    font-size: 12px;
    color: #7f8c8d;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

if tab_selection == "Landing":
    st.title("💷 Prognoza Curs GBP/RON")
    
    col_btn, _ = st.columns([1, 5])
    if col_btn.button("Actualizeaza Date"):
        requests.post(f"{API_URL}/scrape")
        st.info("Cererea de scraping a fost trimisa backend-ului.")

    # KPI Row
    forecast_data = get_data("forecast/latest")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rmse = forecast_data.get("best_rmse") if forecast_data else None
        val = f"{rmse:.4f}" if rmse else "N/A"
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">RMSE (Best Model)</div><div class="kpi-value">{val}</div></div>', unsafe_allow_html=True)
    
    with col2:
        status = forecast_data.get("forecast_status", "N/A") if forecast_data else "Deconectat"
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Status Sistem</div><div class="kpi-value">{status}</div></div>', unsafe_allow_html=True)
        
    with col3:
        winner = forecast_data.get("winner_model") if forecast_data else "N/A"
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Model Castigator</div><div class="kpi-value">{winner}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Grafic istoric
    st.subheader("Evolutie Istorica Curs GBP/RON")
    rates_data = get_data("rates")
    if rates_data:
        df_rates = pd.DataFrame(rates_data)
        df_rates['date'] = pd.to_datetime(df_rates['date'])
        df_rates = df_rates.sort_values('date')
        st.line_chart(df_rates.set_index('date')['gbp_rate'])
    else:
        st.warning("Backend-ul FastAPI nu este accesibil (port 8000). Porniti serverul pentru a vedea graficul.")

elif tab_selection == "Antrenare":
    st.title("📉 Antrenare & Evaluare Modele")
    
    if st.button("Reantreneaza Modele"):
        try:
            res = requests.post(f"{API_URL}/train")
            if res.status_code == 200:
                msg = res.json().get("message", "Comanda trimisa.")
                st.info(msg)
        except:
            st.error("Nu am putut contacta backend-ul.")

    st.subheader("Metrici de Performanta")
    metrics_data = get_data("metrics")
    if metrics_data:
        st.table(pd.DataFrame(metrics_data))
    
    st.markdown("---")
    st.subheader("Vizualizare Hold-Out Forecast")
    
    plot_path = REPORTS_DIR / "forecast_plot.html"
    if os.path.exists(plot_path):
        try:
            with open(plot_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                components.html(html_content, height=600, scrolling=True)
        except Exception as e:
            st.error(f"Eroare la citirea graficului: {e}")
    else:
        st.info("Graficul forecast_plot.html lipseste din folderul reports. Rulati pipeline-ul pentru a-l genera.")

elif tab_selection == "Optuna":
    st.title("🧪 Optimizare Hiperparametri (Optuna)")
    
    st.info("ℹ️ Dashboard-urile Optuna trebuie pornite separat din terminal înainte de a apăsa butoanele de mai jos.")
    
    optuna_links = get_data("optuna-links")
    if optuna_links:
        for link in optuna_links:
            with st.expander(f"Studiu: {link['model']}"):
                col_info, col_link = st.columns([3, 1])
                status = "✅ Disponibil" if link['exists'] else "❌ Lipseste"
                col_info.write(f"**Status DB:** {status}")
                col_info.write(f"**Cale:** `{link['db_path']}`")
                
                if link['exists']:
                    col_link.link_button("🌐 Deschide Dashboard", link['dashboard_url'])
                    st.markdown("**Comanda pornire locala (PowerShell):**")
                    # Construim calea relativa pentru afisare curata
                    db_filename = os.path.basename(link['db_path'])
                    rel_path = f"outputs/optuna_studies/{db_filename}"
                    st.code(f"python -c \"from optuna_dashboard import run_server; run_server('sqlite:///{rel_path}', port={link['port']})\"")
                else:
                    st.info("Rulati 'python run_optuna_optimization.py' pentru a genera studiul.")
    else:
        st.warning("Nu am putut prelua informatiile despre studiile Optuna.")
