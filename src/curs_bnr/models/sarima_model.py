import warnings
import itertools
from typing import (
    Tuple,
    List,
    Dict,
    Any,
    Optional
)
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error
)
from sklearn.model_selection import TimeSeriesSplit
from statsmodels.tsa.statespace.sarimax import SARIMAX
from curs_bnr.config import N_TEST_DAYS

# Ignorăm avertismentele referitoare la convergența rădăcinilor ne-staționare emise intens de Statsmodels
warnings.filterwarnings("ignore")


def calculate_metrics(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Extrage obiectiv triada finală de evaluare stabilită prin Plan.
    """
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = mean_absolute_percentage_error(y_true, y_pred)
    
    return {'MAE': mae, 'RMSE': rmse, 'MAPE': mape}


def tune_sarima(
    train_series: pd.Series,
    p_opt: Optional[List[int]] = None,
    d_opt: Optional[List[int]] = None,
    q_opt: Optional[List[int]] = None,
    P_opt: Optional[List[int]] = None,
    D_opt: Optional[List[int]] = None,
    Q_opt: Optional[List[int]] = None,
    s: int = 7,
    n_splits: int = 2  # Redus de la 3 pentru a accelera CV-ul fără a pierde stabilitatea trendului
) -> Tuple[Any, Tuple[int, int, int], Tuple[int, int, int, int]]:
    """
    Procesează grila de căutare optimizată.
    Optimizare: Reducerea spațiului p,q la [0,1,2] și a iterațiilor CV (maxiter=30) 
    pentru un compromis optim între timpul de antrenare și explorarea parametrizării.
    """
    # Spațiu de căutare extins conform planului de optimizare (Tema 3)
    p_opt = p_opt if p_opt is not None else [0, 1, 2, 3]
    d_opt = d_opt if d_opt is not None else [0, 1]
    q_opt = q_opt if q_opt is not None else [0, 1, 2, 3]
    P_opt = P_opt if P_opt is not None else [0, 1, 2]
    D_opt = D_opt if D_opt is not None else [0, 1]
    Q_opt = Q_opt if Q_opt is not None else [0, 1, 2]

    pdq_combinatii = list(itertools.product(p_opt, d_opt, q_opt))
    seasonal_combinatii = [(x[0], x[1], x[2], s) for x in list(itertools.product(P_opt, D_opt, Q_opt))]
    
    tscv = TimeSeriesSplit(n_splits=n_splits)
    best_rmse = float("inf")
    best_pdq = (0, 0, 0)
    best_seasonal = (0, 0, 0, 0)
    
    print(f"SARIMA Optimization: Investigating {len(pdq_combinatii) * len(seasonal_combinatii)} combinations...")
    
    for pdq in pdq_combinatii:
        for seas in seasonal_combinatii:
            cv_rmse_scores = []
            for train_idx, val_idx in tscv.split(train_series):
                cv_train, cv_val = train_series.iloc[train_idx], train_series.iloc[val_idx]
                try:
                    model = SARIMAX(cv_train, order=pdq, seasonal_order=seas, 
                                    enforce_stationarity=False, enforce_invertibility=False)
                    # maxiter=30 în tuning pentru viteză; suficient pentru a detecta gradul de eroare
                    model_fit = model.fit(disp=False, method='lbfgs', maxiter=30) 
                    cv_pred = model_fit.forecast(steps=len(cv_val))
                    cv_rmse_scores.append(np.sqrt(mean_squared_error(cv_val, cv_pred)))
                except Exception:
                    continue
                    
            if cv_rmse_scores:
                mean_rmse_cv = np.mean(cv_rmse_scores)
                if mean_rmse_cv < best_rmse:
                    best_rmse, best_pdq, best_seasonal = mean_rmse_cv, pdq, seas
    
    print(f"Best SARIMA: {best_pdq}x{best_seasonal} | RMSE CV: {best_rmse:.5f}")
    
    # Fit final cu maxiter=100 pentru convergență completă a modelului ales
    final_model = SARIMAX(train_series, order=best_pdq, seasonal_order=best_seasonal,
                          enforce_stationarity=False, enforce_invertibility=False)
    rezultat_final = final_model.fit(disp=False, maxiter=100)
    
    return rezultat_final, best_pdq, best_seasonal


def predict_out_of_sample(model_fit: Any, steps_viitor: int = N_TEST_DAYS) -> pd.DataFrame:
    """ Generare proiecție cu intervale de încredere (CI 95%). """
    proiectie = model_fit.get_forecast(steps=steps_viitor)
    df_pred = pd.DataFrame({
        'pred_mean': proiectie.predicted_mean,
        'conf_lower': proiectie.conf_int(alpha=0.05).iloc[:, 0],
        'conf_upper': proiectie.conf_int(alpha=0.05).iloc[:, 1]
    })
    return df_pred
