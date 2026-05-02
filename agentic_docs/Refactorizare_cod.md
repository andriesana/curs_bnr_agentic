# Plan de Refactorizare: Arhitectură Profesională `src/curs_bnr`

Acest plan detaliază tranziția de la un set de scripturi laxe la un pachet Python structurat profesional, ușor de testat și de extins.

## 1. Maparea Fișierelor Actuale la Noua Structură

Toată logica de business va fi mutată sub directorul `src/curs_bnr/`.

| Fișier Curent (Root) | Noua Locație | Rol / Modificare |
| :--- | :--- | :--- |
| `scrape_curs.py` | `src/curs_bnr/data/scraper.py` | Funcțiile de extragere BNR. |
| `data_preprocessing.py` | `src/curs_bnr/data/preprocessing.py` | Curățarea, feature engineering și time-series split. |
| `evaluation.py` | `src/curs_bnr/evaluation/metrics.py` | Calculul RMSE, MAPE, și exportul decizional CSV. |
| `model_sarima.py` | `src/curs_bnr/models/sarima_model.py` | Logica de antrenare și prognoză SARIMA. |
| `model_prophet.py` | `src/curs_bnr/models/prophet_model.py` | Logica de antrenare și prognoză Prophet. |
| `model_xgboost.py` | `src/curs_bnr/models/xgboost_model.py` | Logica de antrenare și prognoză XGBoost. |
| `plotting.py` | `src/curs_bnr/visualization/plots.py` | Generarea `forecast_plot.html`. |
| `main_pipeline.py` (nucleul) | `src/curs_bnr/training/pipeline.py` | Aici va sta funcția principală `run_pipeline()`. |
| `run_optuna_optimization.py` (nucleul) | `src/curs_bnr/optimization/optuna_runner.py` | Obiectivele Optuna și crearea studiilor. |
| **[NOU]** | `src/curs_bnr/config.py` | Fișier cu constantele globale (Căi de fișiere, parametri default). |

> **NOTĂ:** În rădăcina proiectului (root) vor fi păstrate doar **scripturile de execuție**, extrem de subțiri (wrappere). Acestea vor importa și lansa codul din `src/`:
> - `main_pipeline.py`
> - `run_optuna_optimization.py`

## 2. Centralizarea Căilor în `config.py` și Structura de Fișiere

Pentru a evita căile "hardcodate" prin multiple scripturi, vom propune un fișier `config.py` care centralizează rutele.
De asemenea, e ideală migrarea fișierelor către un concept de `outputs/` și `data/raw/` (Best Practice).

* **Date de Intrare:** Mutarea datelor extrase din rădăcina folderului `data/` către `data/raw/gbp_curs_bnr.csv` protejează sursa nealterată.
* **Date de Ieșire:** Toate fișierele generate automat vor fi grupate direct sub un folder părinte `outputs/`, având subdirectoarele independente `reports/`, `models/` și `optuna_studies/`. Astfel, în root vom avea un singur director curat pentru toate ieșirile.

```python
# Exemplu src/curs_bnr/config.py
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Căi pentru Date
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "gbp_curs_bnr.csv"

# Căi pentru Ieșiri
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = OUTPUTS_DIR / "reports"
MODELS_DIR = OUTPUTS_DIR / "models"
OPTUNA_STUDIES_DIR = OUTPUTS_DIR / "optuna_studies"
```

## 3. Schimbarea Importurilor

Acum, scripturile din `src/` trebuie să își rezerve un *Namespace* comun (`curs_bnr.`).

**În loc de abordarea veche (Ex: `main_pipeline.py` actual):**
```python
import data_preprocessing as dp
import model_xgboost as mx
import evaluation
```

**Se va folosi abordarea nouă modulară:**
```python
from curs_bnr.config import RAW_DATA_PATH, REPORTS_DIR
from curs_bnr.data import preprocessing as dp
from curs_bnr.models import xgboost_model as mx
from curs_bnr.evaluation import metrics as evaluation
```

Datorită acestei arhitecturi, execuția scripturilor de la nivelul root-ului va recunoaște automat pachetul `curs_bnr`.

## 4. Ce Nu Va Fi Modificat
- Logica matematică a modelelor, TimeSeriesSplit-ul și metricile.
- `pornire_dashboard_optuna.ipynb` (doar vom ajusta calea cu un director în plus dacă decizi să grupăm sub `outputs/`).
- Jurnalele Markdown din `agentic_docs/`.
- Obiectivul de 30/20 trials.

## User Review Required

1. **Aprobare Director `outputs/`:** Ești de acord să grupăm tot ceea ce generează codul sub folderul unic `outputs/` (adică `outputs/reports/` și `outputs/models/`) pentru o curățenie perfectă a rădăcinii?
2. **Aprobare mutare Date:** Ești de acord să mutăm manual `gbp_curs_bnr.csv` în `data/raw/`?
