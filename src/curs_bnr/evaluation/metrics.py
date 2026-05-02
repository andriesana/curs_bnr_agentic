import os
from curs_bnr.config import REPORTS_DIR
import numpy as np
import pandas as pd
from typing import (
    Dict,
    Tuple
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error
)


def evaluate_predictions(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, float]:
    """
    Suprapune valorile prezise pe realitatea oarbă din piață calculând erorile agregate.
    Forțează alinierea strictă a DatetimeIndex-ului pentru a garanta comparativitatea la zi perfectă de tip T+N.

    Args:
        y_true (pd.Series): Seria originală ascunsă reținută izolat pe post de "Test Set" (Adevărul de control).
        y_pred (pd.Series): Seria rezultatelor estimative extrasă din coloana 'pred_mean' a predicțiilor.

    Returns:
        Dict[str, float]: Triada de evaluare izolată standardizată [MAE, RMSE, MAPE].
    """
    # 1. Garanția alinierii superioare de Index - Utilizăm concatenarea pandas ce forțează match pe dată/zi
    # Reducând liniile fără intersectare de index cu `.dropna()` asigurăm raportarea exactă
    aliniament = pd.concat([y_true.rename('Adevar'), y_pred.rename('Predictie')], axis=1).dropna()
    
    if len(aliniament) == 0:
         raise ValueError(
             "Eșec Critic: Nu există nicio suprapunere logică a indecșilor "
             "de timp între Cursul Estimat (Modele) și Piața Reală (Test)!"
         )
            
    val_true = aliniament['Adevar'].values
    val_pred = aliniament['Predictie'].values
    
    # Penalitățile calculate liniar pur
    mae = mean_absolute_error(val_true, val_pred)
    rmse = np.sqrt(mean_squared_error(val_true, val_pred))
    mape = mean_absolute_percentage_error(val_true, val_pred)
    
    return {'MAE': mae, 'RMSE': rmse, 'MAPE': mape}


def compare_all_models(
    dict_predictii: Dict[str, pd.DataFrame], 
    true_test_series: pd.Series
) -> Tuple[str, pd.DataFrame]:
    """
    Preia fluxul de rapoarte din cele 3 module de rețele matematice, conturează concluzia comparativă 
    și stabilește algoritmic Modelul Suprem vizând în totalitate minimizarea pe criteriul judecător absolut (MAPE).

    Args:
        dict_predictii (Dict[str, pd.DataFrame]): Un dicționar decodat dinamic expunând cheia (Denumirea Modelului) 
                                                  și Dataframe-ul specific reținând proiecții.
        true_test_series (pd.Series): Orizontul temporal decupat de Hold-Out-Test (Adevărul Pieței).

    Returns:
        Tuple[str, pd.DataFrame]: 
             1. Denumirea oficializată a Liderului.
             2. DataFrame-ul aglutinat formatând perfect etichetele rețelei 
                versus raportarea numerică decizională propriu-zisă.
    """
    rezultate = []
    
    # Interogarea și conversia penalităților sub fiecare algoritm individual
    for nume_algoritm, format_pred in dict_predictii.items():
        seria_prezisa = format_pred['pred_mean']
        scoruri_calc = evaluate_predictions(true_test_series, seria_prezisa)
        
        # Etichetarea curată a instanțierii specific pentru tabelul de output log reports
        scoruri_calc['Model'] = nume_algoritm
        rezultate.append(scoruri_calc)
        
    df_results = pd.DataFrame(rezultate)
    
    # Restructurare indexată de tip (Subiect -> Observații Evaluare)
    df_results = df_results[['Model', 'MAE', 'RMSE', 'MAPE']]
    
    # Sortare conform cerinței: MAPE (prioritar), apoi RMSE, apoi MAE
    df_results = df_results.sort_values(by=['MAPE', 'RMSE', 'MAE'], ascending=True).reset_index(drop=True)
    
    # Desemnarea absolută a Câștigătorului (după sortare, primul rând este cel mai bun)
    best_model_name = df_results.loc[0, 'Model']
    
    return best_model_name, df_results


def export_metrics_reports(df_metrics: pd.DataFrame, custom_path: str = str(REPORTS_DIR)) -> None:
    """
    Exilează structural prin scriere fizică matricea decizională ierarhică 
    rezultată premergătoare Plotly într-un director de siguranță .csv.

    Args:
        df_metrics (pd.DataFrame): Informația tabelară generată în decizia supremă comparativă.
        custom_path (str): String ce forțează decodificarea rutei relative destinate 
                           mapajului rapoartelor (Implicit fixată agreat la 'reports').
    """
    # Rețeaua operațională forțează crearea logicii directorului fizic 
    # ignorând blocajul erorii recurente in sistemul de baze
    if not os.path.exists(custom_path):
        os.makedirs(custom_path)
        
    fisier_destinatie = os.path.join(custom_path, "metrics_models_comparison_14d.csv")
    
    # Depozitarea nativă liniară CSV lipsită complet de adnotari redundante sub rand de indecși globali false 
    df_metrics.to_csv(fisier_destinatie, index=False)
    
    print(f"[REPORT] Log de evaluare a testului Hold-Out finalizat "
          f"si persistent sub calea standardizata: {fisier_destinatie}")
