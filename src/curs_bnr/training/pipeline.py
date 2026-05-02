import os
import time
import joblib
import pandas as pd
import xgboost as xgb
from prophet import Prophet
from statsmodels.tsa.statespace.sarimax import SARIMAX
from typing import (
    Any,
    Tuple
)

# Importuri din pachetul curs_bnr
from curs_bnr.config import (
    CSV_PATH,
    REPORTS_DIR,
    MODELS_DIR,
    N_TEST_DAYS,
    TARGET_COL,
    CONFIDENCE_INTERVAL
)
from curs_bnr.data import preprocessing as dp
from curs_bnr.models import sarima_model as ms
from curs_bnr.models import prophet_model as mp
from curs_bnr.models import xgboost_model as mx
from curs_bnr.evaluation import metrics as ev
from curs_bnr.visualization import plots as pl


def get_baseline_results(model_name: str, train_data: Any, test_data: Any) -> Tuple[pd.DataFrame, float]:
    """
    Antrenează și evaluează un model folosind configurații de bază (baseline).
    """
    start_time = time.time()
    
    if model_name == "SARIMA":
        # Baseline SARIMA: (1,1,1) fără componentă sezonieră complexă
        model = SARIMAX(train_data, order=(1, 1, 1), seasonal_order=(0, 0, 0, 7), 
                        enforce_stationarity=False, enforce_invertibility=False)
        model_fit = model.fit(disp=False, maxiter=50)
        df_pred = ms.predict_out_of_sample(model_fit, steps_viitor=N_TEST_DAYS)
        
    elif model_name == "PROPHET":
        # Baseline Prophet: Configurație default
        m = Prophet(weekly_seasonality=True, yearly_seasonality=True, interval_width=CONFIDENCE_INTERVAL)
        m.fit(train_data)
        df_pred = mp.predict_out_of_sample(m, steps_viitor=N_TEST_DAYS)
        
    elif model_name == "XGBOOST":
        # Baseline XGBoost: Parametri default
        X_train, y_train = train_data
        X_test = test_data
        model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        
        # Intervalele de bază (dummy pentru baseline, folosind media ca limite daca nu avem regresor quantile)
        df_pred = pd.DataFrame({
            'pred_mean': preds,
            'conf_lower': preds * 0.98,
            'conf_upper': preds * 1.02
        }, index=X_test.index)
        
    execution_time = time.time() - start_time
    return df_pred, execution_time


def save_winning_model(
    model_data: Any, 
    model_name: str, 
    save_full_model: bool = True, 
    models_dir: str = str(MODELS_DIR)
) -> None:
    """ Salvează modelul câștigător pe disc (opțional). """
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        
    file_path = os.path.join(models_dir, f"best_model_{model_name.lower()}.joblib")
    
    if save_full_model:
        joblib.dump(model_data, file_path)
        print(f"[SAVE] [SAVED] Modelul complet a fost salvat in: {file_path}")
    else:
        print(f"[SKIP] [SKIPPED] Salvarea modelului complet a fost sarita conform setarilor.")


def run_pipeline(csv_path: str = str(CSV_PATH)) -> None:
    """ Orchestrează fluxul complet cu raportare Baseline vs Optimizat. """
    print(f"[START] Initializare Pipeline de Prognoza BNR (Tema 3 - Optimizare)...")

    # 1. Preprocesare Date
    df_raw = dp.load_and_impute_data(csv_path)
    df_feat = dp.create_features(df_raw)
    train_df, test_df = dp.split_temporal_data(df_feat, test_days=N_TEST_DAYS)
    y_test_real = test_df[TARGET_COL]
    
    # Rezultate pentru raportul de optimizare
    optimization_results = []
    # Colector pentru varianta "Câștigătoare" a fiecărui model (pentru selecția finală)
    optimized_predictions = {}
    optimized_objects = {}

    # --- MODELE ---
    model_list = ["SARIMA", "PROPHET", "XGBOOST"]

    for m_name in model_list:
        print(f"\n--- Analiza Model: {m_name} ---")
        
        # A. RULARE BASELINE
        if m_name == "XGBOOST":
            X_tr, y_tr = mx.prepare_xgb_data(train_df, target_col=TARGET_COL)
            X_ts, _ = mx.prepare_xgb_data(test_df, target_col=TARGET_COL)
            pred_base, t_base = get_baseline_results(m_name, (X_tr, y_tr), X_ts)
        elif m_name == "PROPHET":
            train_prophet = mp.prepare_prophet_data(train_df, target_col=TARGET_COL)
            pred_base, t_base = get_baseline_results(m_name, train_prophet, None)
        else: # SARIMA
            pred_base, t_base = get_baseline_results(m_name, train_df[TARGET_COL], None)
            
        metrics_base = ev.evaluate_predictions(y_test_real, pred_base['pred_mean'])
        optimization_results.append({
            'Model': m_name, 'Variant': 'Baseline',
            'RMSE': metrics_base['RMSE'], 'MAPE': metrics_base['MAPE'], 'Time (s)': t_base
        })

        # B. RULARE OPTIMIZAT
        t_opt_start = time.time()
        if m_name == "SARIMA":
            best_fit, _, _ = ms.tune_sarima(train_df[TARGET_COL])
            pred_opt = ms.predict_out_of_sample(best_fit, steps_viitor=N_TEST_DAYS)
            obj_opt = best_fit
        elif m_name == "PROPHET":
            best_m, _ = mp.tune_prophet(train_prophet, n_trials=10)
            pred_opt = mp.predict_out_of_sample(best_m, steps_viitor=N_TEST_DAYS)
            obj_opt = best_m
        else: # XGBOOST
            params_opt = mx.tune_xgboost(X_tr, y_tr, n_trials=50)
            pred_opt = mx.predict_out_of_sample(params_opt, X_tr, y_tr, X_ts)
            # Re-antrenăm ansamblul câștigător pentru salvare
            obj_opt = {
                'params': params_opt,
                'mean': xgb.XGBRegressor(**params_opt).fit(X_tr, y_tr),
                'low': xgb.XGBRegressor(
                    objective='reg:quantileerror', quantile_alpha=0.05, **params_opt
                ).fit(X_tr, y_tr),
                'high': xgb.XGBRegressor(
                    objective='reg:quantileerror', quantile_alpha=0.95, **params_opt
                ).fit(X_tr, y_tr)
            }
            
        t_opt = time.time() - t_opt_start
        metrics_opt = ev.evaluate_predictions(y_test_real, pred_opt['pred_mean'])
        
        # Calcul Improvement fata de baseline propriu
        imp = ((metrics_base['MAPE'] - metrics_opt['MAPE']) / metrics_base['MAPE']) * 100
        
        optimization_results.append({
            'Model': m_name, 'Variant': 'Optimized',
            'RMSE': metrics_opt['RMSE'], 'MAPE': metrics_opt['MAPE'], 
            'Time (s)': t_opt, 'Improvement %': imp
        })
        
        optimized_predictions[m_name] = pred_opt
        optimized_objects[m_name] = obj_opt

    # --- RAPORTARE SI SELECTIE ---
    df_opt_report = pd.DataFrame(optimization_results)
    print("\n[REPORT] RAPORT OPTIMIZARE (Baseline vs Optimized):")
    print(df_opt_report.to_string(index=False))
    
    # Salvare raport optimizare
    if not os.path.exists(str(REPORTS_DIR)): 
        os.makedirs(str(REPORTS_DIR))
    
    report_file = os.path.join(str(REPORTS_DIR), "optimization_comparison.csv")
    df_opt_report.to_csv(report_file, index=False)

    # Selecție Campion Final dintre cele optimizate
    best_overall_name, final_metrics = ev.compare_all_models(optimized_predictions, y_test_real)
    print(f"\n[WINNER] CAMPIONUL FINAL: {best_overall_name}")
    print(final_metrics)

    # Vizualizare și Salvare
    pl.plot_forecast_results(
        y_test_real, 
        optimized_predictions[best_overall_name], 
        best_overall_name, 
        y_hist=train_df[TARGET_COL].tail(30)
    )
    
    save_winning_model(
        optimized_objects[best_overall_name], 
        best_overall_name, 
        save_full_model=True,
        models_dir=str(MODELS_DIR)
    )
    
    print(f"\n[DONE] Pipeline finalizat. Rezultate in '{REPORTS_DIR}' si '{MODELS_DIR}'.")


def main() -> None:
    """ Punct de intrare pentru execuția pipeline-ului. """
    if os.path.exists(str(CSV_PATH)):
        run_pipeline()
    else:
        # Căutăm și în locația veche pentru tranziție, dacă CSV_PATH (data/raw) e gol
        if os.path.exists("data/gbp_curs_bnr.csv"):
             run_pipeline("data/gbp_curs_bnr.csv")
        else:
             print(f"[ERROR] Sursa date lipsa la calea: {CSV_PATH}")


if __name__ == "__main__":
    main()
