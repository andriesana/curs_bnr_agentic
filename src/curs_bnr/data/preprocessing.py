from curs_bnr.config import N_TEST_DAYS
import pandas as pd
from typing import Tuple


def load_and_impute_data(file_path: str) -> pd.DataFrame:
    """
    Încarcă setul de date din format CSV, resetează indexul temporal
    pentru o periodicitate zilnică și tratează valorile lipsă (gap-urile).

    Args:
        file_path (str): Calea către fișierul CSV de intrare.

    Returns:
        pd.DataFrame: Dataframe-ul cu index de timp validat și golurile acoperite folosind metoda ffill.
    """
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Asigurăm ordinea crescătoare
    df.sort_index(inplace=True)
    
    # Aplicăm grila zilnică - extinde vectorul calendaristic și introduce NaN pe zilele moarte (de weekend)
    df = df.asfreq('D')
    
    # Forward-Fill: Valoarea raportată Vineri intră pe hold și suplinește fix Sâmbătă și Duminică
    df['gbp_rate'] = df['gbp_rate'].ffill()
    
    return df


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construiește atribute secundare de corelație temporală (Feature Engineering), 
    menținând constantă alinierea și ținta "gbp_rate".

    Coloane returnate în DataFrame:
        - gbp_rate (float): Ținta originală (Variabila dependentă vizată de predicție).
        - dayofweek (int): Ziua din săptămână (0=Luni, 6=Duminică).
        - lag_1 (float): Cursul decalat preluat din ziua precedentă (T-1).
        - lag_3 (float): Cursul de acum 3 zile (T-3).
        - lag_7 (float): Cursul de acum o săptămână precisă (T-7).
        - ma_7 (float): Media mobilă istorică calculată pe ultimele 7 zile anterioare.
        - ma_14 (float): Media mobilă istorică trasată fix pentru ultimele 14 zile.

    Args:
        df (pd.DataFrame): Dataframe-ul original supus la 'asfreq' / 'ffill'.

    Returns:
        pd.DataFrame: Tabela adnotată complet cu noile atribute. Pentru aliniere ireproșabilă,
                      instanțele purtând NaN pe zonele de shiftare inițiale sunt reduse via 'dropna()'.
    """
    df_feat = df.copy()
    
    # 1. Obținem features de calendar standard
    df_feat['dayofweek'] = df_feat.index.dayofweek
    
    # 2. Defalcarea întreruperilor liniare absolute (Lags)
    df_feat['lag_1'] = df_feat['gbp_rate'].shift(1)
    df_feat['lag_3'] = df_feat['gbp_rate'].shift(3)
    df_feat['lag_7'] = df_feat['gbp_rate'].shift(7)
    
    # 3. Formtarea Mediilor Mobile Explicite (pe structură de la t-1)
    # ATENȚIE (Fără Data Leakage): Se aplică mediile mobile calculând din shift-ul anterior. 
    # Dacă aplicam rolling pe gbp_rate direct, calculam media adăugând rezultatul viitor
    # și distrugeam validarea din viitor!
    rata_decalata_istoric = df_feat['gbp_rate'].shift(1)
    df_feat['ma_7'] = rata_decalata_istoric.rolling(window=7).mean()
    df_feat['ma_14'] = rata_decalata_istoric.rolling(window=14).mean()
    
    # 4. Eliminarea completă a zonelor unde matematica nu operează vizionar 
    # (lipsesc primele 14 capete superioare din istoric)
    df_feat.dropna(inplace=True)
    
    return df_feat


def split_temporal_data(df: pd.DataFrame, test_days: int = N_TEST_DAYS) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Decupează logic secvența ascuțită finală a seriei drept Test Suprem neaccesibil 
    pentru mașinile de antrenament și tuning.

    Args:
        df (pd.DataFrame): Dataframe-ul consolidat, curat și cu atribute derivate.
        test_days (int): Pragul strict de secundație / ultimele zile (Default este 14).

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Sistem secvențiat compus din Train limitat superior (Istoricul amplu), 
                                           alături de sub-gruparea izolată finală pe ultimele T `test_days`.
    """
    if len(df) <= test_days:
        raise ValueError(f"Setul principal de date este precar (conține {len(df)} elemente < testare {test_days}).")
        
    train_df = df.iloc[:-test_days].copy()
    test_df = df.iloc[-test_days:].copy()
    
    return train_df, test_df
