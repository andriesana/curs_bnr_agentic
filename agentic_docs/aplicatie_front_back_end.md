# Plan Extensie Full-Stack: Prognoză GBP/RON

## Scop
Acest document detaliază arhitectura pentru o extensie full-stack a proiectului de previziune a cursului valutar GBP/RON, integrând interfețe moderne de utilizator și un sistem robust de tip backend. Soluția propune:
- Crearea unei aplicații web complete (front end + back end) destinate urmăririi și prognozei cursului valutar GBP/RON.
- Integrarea unei baze de date **SQLite** unificate, capabile să stocheze:
  - Istoricul complet al antrenărilor, incluzând modelul câștigător, parametrii optimizați salvați în format JSON, metricile de evaluare (RMSE, MAE, MAPE) și timestamp-ul (data rulării).
  - Datele istorice oficiale extrase pentru cursul GBP/RON.
  - Prognozele istorice (rezultatele viitoare generate de cel mai bun model la fiecare rulare).
- Oferirea unui backend funcțional care să poată efectua *web scraping* la cerere pe site-ul BNR și să actualizeze automat structura bazei de date.

## Rol
- **Proiectare arhitecturală:** Dezvoltarea unei aplicații Python full-stack, decuplată logic și ușor de întreținut.
- **Design UX/UI:** Realizarea unei experiențe de utilizare impecabile pentru interfața Streamlit, punând accent pe claritatea datelor financiare.
- **Design Bază de Date:** Structurarea logică a tabelelor, a relațiilor dintre ele (ex: legătura dintre o antrenare și prognoza sa aferentă) și stabilirea logicii pentru menținerea pe termen lung a istoricului.

---

## Cerințe

### Front end (Streamlit)
Interfața vizuală va fi dezvoltată folosind **Streamlit** și va asigura următoarele:
- **Landing Page (Dashboard Principal):** Va afișa prognoza curentă GBP/RON, istoricul interactiv al cursului și un KPI clar care să indice eroarea medie pe ultimele 14 zile.
- **Tab Antrenament & Performanță:** O vizualizare a rezumatului ultimei antrenări, integrând graficul HTML deja existent (`reports/forecast_plot.html`) pentru evaluarea alinierii vizuale a predicției.
- **Tab Optimizare Optuna:** Secțiune dedicată cu instrucțiuni și butoane (link-uri rapide) pentru a accesa direct panoul *Optuna Dashboard*, făcând legătura cu studiile `.db` din `reports/optuna_studies`.
- **Indicator Trend Eroare:** Un mecanism vizual simplu (Săgeată Sus / Săgeată Jos / Linie Orizontală) care va semnala trendul erorii RMSE: crescător, descrescător sau neschimbat față de antrenarea precedentă.

### Back end (FastAPI)
Logica de business și comunicarea de date vor fi susținute de **FastAPI**, incluzând:
- **Conectare SQLite:** Gestionarea sesiunilor și a tranzacțiilor SQL în mod asincron și sigur.
- Un endpoint de tip `GET` pentru citirea și livrarea datelor istorice serializate JSON.
- Un endpoint de tip `POST` pentru declanșarea scraperului (actualizarea cursbnr.ro).
- Un endpoint de tip `POST` capabil să pornească / re-ruleze asincron antrenarea modelelor (`main_pipeline`).
- Un endpoint de tip `GET` pentru servirea exclusivă a celei mai recente prognoze (pentru integrare rapidă în landing page).

---

## Baza de date propusă (SQLite)

Arhitectura relațională pentru păstrarea metadatelor și a valorilor va conține 4 tabele majore:

1. **`exchange_rates`**
   - *Rol:* Stocarea istoricului real (valori scraper).
   - *Câmpuri:* `id` (PK), `date` (Data valutară YYYY-MM-DD), `rate` (Valoarea GBP în RON), `inserted_at` (Timestamp preluare).

2. **`training_runs`**
   - *Rol:* Evidența fiecărei rulări de optimizare/antrenare (run).
   - *Câmpuri:* `id` (PK), `run_date` (Când a fost executată), `status` (Ex: success, failed).

3. **`model_results`**
   - *Rol:* Detalii de performanță pentru fiecare model antrenat într-un anumit run.
   - *Câmpuri:* `id` (PK), `run_id` (FK -> training_runs.id), `model_name` (Ex: XGBoost, Prophet), `best_params` (Text JSON), `rmse` (Float), `mae` (Float), `mape` (Float), `is_champion` (Boolean).

4. **`forecasts`**
   - *Rol:* Arhivarea prognozelor extrase, pentru comparare ulterioară cu piața reală.
   - *Câmpuri:* `id` (PK), `model_id` (FK -> model_results.id), `target_date` (Data pentru care s-a făcut predicția), `predicted_rate` (Valoarea GBP prognozată).

---

> **Observație:** Acest document reprezintă exclusiv planul de arhitectură propus pentru dezvoltarea viitoare (Extensie Full-Stack Tema 3+). La acest moment, niciun cod Python frontend/backend nu a fost implementat, iar structura actuală modulară locală rămâne intactă.
