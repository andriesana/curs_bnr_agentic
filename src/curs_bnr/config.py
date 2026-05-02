"""
Configurații globale și rute pentru proiectul de previziune a cursului valutar BNR.
"""
from pathlib import Path

# Căi Globale și de Arhitectură
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Căi pentru Date
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
CSV_FILENAME = "gbp_curs_bnr.csv"
CSV_PATH = DATA_RAW_DIR / CSV_FILENAME

# Căi pentru Ieșiri
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = OUTPUTS_DIR / "reports"
MODELS_DIR = OUTPUTS_DIR / "models"
OPTUNA_STUDIES_DIR = OUTPUTS_DIR / "optuna_studies"

# Constante și Parametri Modelare
N_TEST_DAYS = 14
TARGET_COL = "gbp_rate"
LAG_DAYS = [1, 3, 7]
ROLLING_WINDOWS = [7, 14]
CONFIDENCE_INTERVAL = 0.95
