import pandas as pd
import numpy as np
from typing import (
    Tuple,
    Dict,
    Any
)
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import optuna
from curs_bnr.config import N_TEST_DAYS, CONFIDENCE_INTERVAL


def prepare_prophet_data(df: pd.DataFrame, target_col: str = 'gbp_rate') -> pd.DataFrame:
    """ Pregătirea formatului ds/y specific Prophet. """
    return pd.DataFrame({'ds': df.index, 'y': df[target_col].values})


def objective(trial: optuna.Trial, train_df: pd.DataFrame) -> float:
    """
    Funcția obiectiv pentru Optuna care optimizează hiperparametrii Prophet.
    Minimizează RMSE mediu rezultat din cross_validation nativ.
    """
    params = {
        'changepoint_prior_scale': trial.suggest_float('changepoint_prior_scale', 0.001, 0.5, log=True),
        'seasonality_prior_scale': trial.suggest_float('seasonality_prior_scale', 0.01, 10.0, log=True),
        'seasonality_mode': trial.suggest_categorical('seasonality_mode', ['additive', 'multiplicative'])
    }
    
    try:
        # Setăm seed-ul pentru numpy pentru a ajuta la reproductibilitatea determinării changepoints
        np.random.seed(42)
        
        m = Prophet(
            **params,
            weekly_seasonality=True,
            yearly_seasonality=True,
            daily_seasonality=False,
            interval_width=CONFIDENCE_INTERVAL
        )
        m.fit(train_df)
        
        # Cross-validation nativ Prophet
        # horizon adaptat conform config.py
        df_cv = cross_validation(
            m, 
            initial='730 days', 
            period='30 days', 
            horizon=f'{N_TEST_DAYS} days', 
            disable_tqdm=True
        )
        
        res = performance_metrics(df_cv)
        return float(res['rmse'].mean())
        
    except Exception:
        # Returnăm un RMSE mare pentru a evita blocarea execuției
        return float('inf')


def tune_prophet(
    train_df: pd.DataFrame,
    n_trials: int = 10
) -> Tuple[Any, Dict[str, Any]]:
    """
    Tuning Prophet folosind Optuna în locul GridSearch.
    """
    print(f"Incepe Tuning-ul Prophet folosind Optuna ({n_trials} trials)...")

    # Dezactivăm logarea excesivă Optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    # Fixăm seed-ul sampler-ului pentru reproductibilitatea căutării
    study = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(lambda trial: objective(trial, train_df), n_trials=n_trials)

    print(f"[DONE] Tuning Prophet finalizat. Cel mai bun RMSE CV: {study.best_value:.5f}")
    
    # Re-antrenăm modelul final cu cei mai buni parametri găsiți
    final_model = Prophet(
        **study.best_params,
        weekly_seasonality=True,
        yearly_seasonality=True,
        daily_seasonality=False,
        interval_width=CONFIDENCE_INTERVAL
    )
    final_model.fit(train_df)
    
    return final_model, study.best_params


def predict_out_of_sample(prophet_model: Any, steps_viitor: int = N_TEST_DAYS) -> pd.DataFrame:
    """
    Generează prognoza Prophet și intervalele de încredere pe orizontul setat.
    Păstrează compatibilitatea cu restul pipeline-ului.
    """
    viitorul = prophet_model.make_future_dataframe(periods=steps_viitor, freq='D')
    forecast = prophet_model.predict(viitorul)
    
    # Decupăm doar orizontul de test/prognoză
    res = forecast.tail(steps_viitor).copy()
    
    df_pred = pd.DataFrame({
        'pred_mean': res['yhat'].values,
        'conf_lower': res['yhat_lower'].values,
        'conf_upper': res['yhat_upper'].values
    }, index=pd.to_datetime(res['ds'].values))
    
    return df_pred
