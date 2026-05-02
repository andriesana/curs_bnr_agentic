import os
import optuna
import pandas as pd
import numpy as np
import xgboost as xgb
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error

# Importuri din pachetul curs_bnr
from curs_bnr.config import (
    CSV_PATH,
    OPTUNA_STUDIES_DIR,
    N_TEST_DAYS,
    TARGET_COL,
    CONFIDENCE_INTERVAL
)
from curs_bnr.data import preprocessing as dp
from curs_bnr.models import xgboost_model as mx
from curs_bnr.models import prophet_model as mp


def objective_xgboost(trial: optuna.Trial, X: pd.DataFrame, y: pd.Series, n_splits: int = 3) -> float:
    """ Obiectiv Optuna pentru optimizarea hiperparametrilor XGBoost pe TimeSeriesSplit. """
    params = {
        'learning_rate': trial.suggest_float('learning_rate', 1e-3, 0.3, log=True),
        'max_depth': trial.suggest_int('max_depth', 3, 9),
        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
        'gamma': trial.suggest_float('gamma', 1e-8, 1.0, log=True),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'objective': 'reg:squarederror',
        'random_state': 42,
        'n_jobs': -1
    }

    tscv = TimeSeriesSplit(n_splits=n_splits)
    cv_scores = []
    
    for train_idx, val_idx in tscv.split(X):
        X_train_cv, y_train_cv = X.iloc[train_idx], y.iloc[train_idx]
        X_val_cv, y_val_cv = X.iloc[val_idx], y.iloc[val_idx]

        model = xgb.XGBRegressor(**params)
        model.fit(X_train_cv, y_train_cv)
        y_pred = model.predict(X_val_cv)
        cv_scores.append(np.sqrt(mean_squared_error(y_val_cv, y_pred)))

    return float(np.mean(cv_scores))


def objective_prophet(trial: optuna.Trial, train_df: pd.DataFrame) -> float:
    """ Obiectiv Optuna pentru Prophet evaluat prin cross-validarea nativă. """
    params = {
        'changepoint_prior_scale': trial.suggest_float('changepoint_prior_scale', 0.001, 0.5, log=True),
        'seasonality_prior_scale': trial.suggest_float('seasonality_prior_scale', 0.01, 10.0, log=True),
        'seasonality_mode': trial.suggest_categorical('seasonality_mode', ['additive', 'multiplicative'])
    }
    
    try:
        np.random.seed(42)
        m = Prophet(
            **params, 
            weekly_seasonality=True, 
            yearly_seasonality=True, 
            daily_seasonality=False,
            interval_width=CONFIDENCE_INTERVAL
        )
        m.fit(train_df)
        
        # Validare nativă pe perioade prestabilite
        df_cv = cross_validation(
            m, initial='730 days', period='30 days', horizon=f'{N_TEST_DAYS} days', disable_tqdm=True
        )
        res = performance_metrics(df_cv)
        return float(res['rmse'].mean())
    except Exception:
        return float('inf')


def objective_sarima(trial: optuna.Trial, train_series: pd.Series, n_splits: int = 2) -> float:
    """ Obiectiv Optuna pentru SARIMA folosind TimeSeriesSplit și maxiter redus pentru eficiență. """
    p = trial.suggest_int('p', 0, 3)
    d = trial.suggest_int('d', 0, 1)
    q = trial.suggest_int('q', 0, 3)
    
    P = trial.suggest_int('P', 0, 2)
    D = trial.suggest_int('D', 0, 1)
    Q = trial.suggest_int('Q', 0, 2)
    s = 7  # Sezonalitate săptămânală
    
    tscv = TimeSeriesSplit(n_splits=n_splits)
    cv_scores = []
    
    for train_idx, val_idx in tscv.split(train_series):
        cv_train, cv_val = train_series.iloc[train_idx], train_series.iloc[val_idx]
        try:
            model = SARIMAX(cv_train, order=(p, d, q), seasonal_order=(P, D, Q, s), 
                            enforce_stationarity=False, enforce_invertibility=False)
            model_fit = model.fit(disp=False, method='lbfgs', maxiter=30) 
            cv_pred = model_fit.forecast(steps=len(cv_val))
            cv_scores.append(np.sqrt(mean_squared_error(cv_val, cv_pred)))
        except Exception:
            cv_scores.append(float('inf'))
            
    if not cv_scores or float('inf') in cv_scores:
        return float('inf')
    
    return float(np.mean(cv_scores))


def main(csv_path: str = str(CSV_PATH)) -> None:
    """ 
    Rularea izolată a optimizării hiperparametrilor folosind stocare SQLite.
    Nu re-antrenează modelul final și nu exportă .joblib, salvează doar metadatele studiilor.
    """
    if not os.path.exists(csv_path):
        # Fallback pentru tranzitie
        if os.path.exists("data/gbp_curs_bnr.csv"):
            csv_path = "data/gbp_curs_bnr.csv"
        else:
            print(f"[ERROR] Sursa date lipsa la calea: {csv_path}")
            return

    # Încărcare și preprocesare standardizată
    df_raw = dp.load_and_impute_data(csv_path)
    df_feat = dp.create_features(df_raw)
    train_df, _ = dp.split_temporal_data(df_feat, test_days=N_TEST_DAYS)
    
    # Asigură existența directorului
    os.makedirs(str(OPTUNA_STUDIES_DIR), exist_ok=True)
    
    # Dezactivare avertismente Optuna abundente
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    # --- XGBoost ---
    print("\n" + "="*50)
    print("[START] Incepere Optimizare XGBoost")
    X_tr, y_tr = mx.prepare_xgb_data(train_df, target_col=TARGET_COL)
    xgb_db = f"sqlite:///{os.path.join(str(OPTUNA_STUDIES_DIR), 'xgboost_optimization.db')}"
    study_xgb = optuna.create_study(
        study_name="xgb_study", storage=xgb_db, direction='minimize', load_if_exists=True
    )
    study_xgb.optimize(lambda trial: objective_xgboost(trial, X_tr, y_tr), n_trials=30)
    print(f"[SUCCESS] XGBoost Finalizat:")
    print(f"   Best RMSE: {study_xgb.best_value:.5f}")
    print(f"   Best Params: {study_xgb.best_params}")
    print(f"   Database: {xgb_db}")

    # --- Prophet ---
    print("\n" + "="*50)
    print("[START] Incepere Optimizare Prophet")
    train_prophet = mp.prepare_prophet_data(train_df, target_col=TARGET_COL)
    prophet_db = f"sqlite:///{os.path.join(str(OPTUNA_STUDIES_DIR), 'prophet_optimization.db')}"
    study_prophet = optuna.create_study(
        study_name="prophet_study", storage=prophet_db, direction='minimize', load_if_exists=True
    )
    study_prophet.optimize(lambda trial: objective_prophet(trial, train_prophet), n_trials=20)
    print(f"[SUCCESS] Prophet Finalizat:")
    print(f"   Best RMSE: {study_prophet.best_value:.5f}")
    print(f"   Best Params: {study_prophet.best_params}")
    print(f"   Database: {prophet_db}")

    # --- SARIMA ---
    print("\n" + "="*50)
    print("[START] Incepere Optimizare SARIMA")
    sarima_series = train_df[TARGET_COL]
    sarima_db = f"sqlite:///{os.path.join(str(OPTUNA_STUDIES_DIR), 'sarima_optimization.db')}"
    study_sarima = optuna.create_study(
        study_name="sarima_study", storage=sarima_db, direction='minimize', load_if_exists=True
    )
    study_sarima.optimize(lambda trial: objective_sarima(trial, sarima_series), n_trials=20)
    print(f"[SUCCESS] SARIMA Finalizat:")
    print(f"   Best RMSE: {study_sarima.best_value:.5f}")
    print(f"   Best Params: {study_sarima.best_params}")
    print(f"   Database: {sarima_db}")

    print("\n" + "="*50)
    print("[INFO] Puteti vizualiza rezultatele ruland in terminal (ex.):")
    print(f"   optuna-dashboard {xgb_db}")


if __name__ == "__main__":
    main()
