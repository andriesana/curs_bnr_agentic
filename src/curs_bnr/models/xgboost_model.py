import pandas as pd
import numpy as np
from typing import (
    Tuple,
    Dict,
    Any
)
import xgboost as xgb
import optuna
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error
from curs_bnr.config import TARGET_COL


def prepare_xgb_data(df: pd.DataFrame, target_col: str = TARGET_COL) -> Tuple[pd.DataFrame, pd.Series]:
    """ Separare features (X) de target (y). """
    return df.drop(columns=[target_col]), df[target_col]


def objective(trial: optuna.Trial, X: pd.DataFrame, y: pd.Series, n_splits: int) -> float:
    """
    Funcția obiectiv pentru Optuna care optimizează hiperparametrii XGBoost.
    Minimizează RMSE obținut prin TimeSeriesSplit.
    """
    params = {
        'learning_rate': trial.suggest_float('learning_rate', 1e-2, 0.3, log=True),
        'max_depth': trial.suggest_int('max_depth', 4, 7),
        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
        'gamma': trial.suggest_float('gamma', 1e-8, 1.0, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
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
        
        score = np.sqrt(mean_squared_error(y_val_cv, y_pred))
        cv_scores.append(score)

    return np.mean(cv_scores)


def tune_xgboost(
    X: pd.DataFrame,
    y: pd.Series,
    n_trials: int = 50,
    n_splits: int = 3
) -> Dict[str, Any]:
    """
    Tuning XGBoost folosind Optuna în locul GridSearch.
    """
    print(f"Incepe Tuning-ul XGBoost folosind Optuna ({n_trials} trials)...")

    # Dezactivăm logarea excesivă Optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    study = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(lambda trial: objective(trial, X, y, n_splits), n_trials=n_trials)

    print(f"[DONE] Tuning XGBoost finalizat. Cel mai bun RMSE: {study.best_value:.5f}")
    return study.best_params


def predict_out_of_sample(
    best_params: Dict[str, Any],
    X_train: pd.DataFrame, 
    y_train: pd.Series, 
    X_test: pd.DataFrame
) -> pd.DataFrame:
    """
    Generează predicția punctuală și intervalele de încredere (Quantile Regression) XGBoost.
    Respectă structura de date agreată: [pred_mean, conf_lower, conf_upper].
    """
    # Adăugăm parametrii de bază fixați
    final_params = best_params.copy()
    final_params.update({'random_state': 42})

    # Model pentru media punctuală
    model_mean = xgb.XGBRegressor(objective='reg:squarederror', **final_params)
    model_mean.fit(X_train, y_train)
    pred_mean = model_mean.predict(X_test)
    
    # Modele pentru intervale (Quantile Regression)
    # Păstrăm valorile quantile_alpha explicite (0.05 și 0.95) conform solicitării
    model_low = xgb.XGBRegressor(objective='reg:quantileerror', quantile_alpha=0.05, **final_params)
    model_high = xgb.XGBRegressor(objective='reg:quantileerror', quantile_alpha=0.95, **final_params)
    
    model_low.fit(X_train, y_train)
    model_high.fit(X_train, y_train)
    
    low = model_low.predict(X_test)
    high = model_high.predict(X_test)
    
    # Prevenția Crossover-ului (conf_lower <= conf_upper)
    return pd.DataFrame({
        'pred_mean': pred_mean,
        'conf_lower': np.minimum(low, high),
        'conf_upper': np.maximum(low, high)
    }, index=X_test.index)
