# Plan de Implementare: Tuning Optuna cu Salvare SQLite (Optuna Dashboard)

## Scopul Modificării
Crearea unui mecanism independent prin care se rulează studiile de optimizare (Hyperparameter Tuning) pentru cele 3 modele de prognoză a cursului GBP/RON (XGBoost, Prophet și SARIMA). Pentru a oferi transparență și posibilitatea de a folosi `optuna-dashboard`, rezultatele vor fi salvate direct pe disc, în fișiere de tip bază de date `SQLite`.

## 1. Arhitectura Fișierelor
- **[NEW] `run_optuna_optimization.py`**: Un script de orchestrare independent plasat în rădăcina proiectului. Va importa datele curățate și va defini funcțiile obiectiv Optuna pentru cele 3 modele.
- **[NEW] `outputs/optuna_studies/`**: Un sub-folder nou creat în interiorul `outputs/` dedicat exclusiv salvării bazelor de date.
- Fără a șterge fișiere de cod existente; structura și preprocesarea rămân fixate pe `data/raw/gbp_curs_bnr.csv`.

## 2. Configurația Optuna și a Modelelor

### Optimizare XGBoost
- **Metodologie CV**: `TimeSeriesSplit` (pentru a evita scurgerile din viitor în trecut).
- **Parametri**: `learning_rate`, `max_depth`, `n_estimators`, `gamma`, `subsample` etc.
- **Durată Tuning**: 30 trials.
- **Stocare**: `sqlite:///outputs/optuna_studies/xgboost_optimization.db` (Study: `xgb_study`).
- **Metrică principală**: RMSE.

### Optimizare SARIMA
- **Metodologie CV**: Buclă `TimeSeriesSplit` antrenând modelul cu un număr rezonabil de iterații (maxiter=30) pentru a menține viteza.
- **Parametri**: Trecem de la `GridSearch` / `itertools` la o căutare inteligentă cu Optuna: `p (0-3)`, `d (0-1)`, `q (0-3)` și componentele sezoniere `P, D, Q`.
- **Durată Tuning**: 20 trials (spațiul de căutare este vast, dar TPE Optuna ajunge repede la parametri buni).
- **Stocare**: `sqlite:///outputs/optuna_studies/sarima_optimization.db` (Study: `sarima_study`).
- **Metrică principală**: RMSE.

### Optimizare Prophet
- **Metodologie CV**: Funcția nativă `cross_validation` din Prophet.
- **Parametri**: `changepoint_prior_scale`, `seasonality_prior_scale`, `seasonality_mode`.
- **Durată Tuning**: 20 trials.
- **Stocare**: `sqlite:///outputs/optuna_studies/prophet_optimization.db` (Study: `prophet_study`).
- **Metrică principală**: RMSE (preluat din `performance_metrics`).

## 3. Strategia de Implementare (run_optuna_optimization.py)
Scriptul va avea un flux clar:
1. Creează directorul `outputs/optuna_studies` dacă nu există.
2. Încarcă datele prin `load_and_impute_data()` și generează atributele decise anterior.
3. Decupează ultimele 14 zile conform regulii curente din proiect.
4. Va executa pe rând:
   - `run_xgboost_study(train_df)`
   - `run_prophet_study(train_df)`
   - `run_sarima_study(train_df)`
5. La final, va afișa un mesaj cu comanda recomandată pentru pornirea serverului local de Dashboard: 
   `optuna-dashboard sqlite:///outputs/optuna_studies/xgboost_optimization.db`

> [!NOTE] 
> Funcțiile obiectiv vor fi integrate direct în acest script pentru modularitate și independență, prevenind supraîncărcarea funcțiilor din fișierele de model_*.py existente.

## Întrebare pentru utilizator / Feedback
Ești de acord să izolez întreaga logică a obiectivelor și a stocării (crearea bazelor sqlite) doar în interiorul lui `run_optuna_optimization.py` pentru a putea executa optimizarea strict atunci când ai nevoie de vizualizare, lăsând restul ecosistemului actual (main pipeline) neatins? Aștept aprobarea ta pentru a implementa acest script.
