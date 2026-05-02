# Previziunea Cursului Valutar BNR (GBP/RON) - Optimizare Modele

Acest proiect reprezintă un flux complet de tip Machine Learning conceput pentru extracția (scraping), curățarea și previzionarea cursurilor valutare oficiale publicate de BNR (cu accent pe paritatea GBP/RON). Proiectul implementează un pipeline modularizat, având ca scop final determinarea celui mai performant model pe baza erorii medii pătratice (RMSE).

## 🧠 Modele Implementate
În cadrul acestui experiment se antrenează și se optimizează 3 algoritmi diferiți, fiecare aducând o abordare unică asupra analizei seriilor de timp:
1. **SARIMA** (Modelare statistică clasică autoregresivă integrată, cu componentă de sezonalitate)
2. **Prophet** (Model aditiv dezvoltat de Meta, robust la date lipsă și eficient în captarea multiplelor sezonalități)
3. **XGBoost** (Gradient boosting regressor, bazat pe arbori decizionali și lag features și medii mobile)

---

## 🚀 Ghid de Rulare

### 1. Rularea Pipeline-ului Principal
Pentru a încărca datele, a executa arhitectura standard comparativă (Baseline vs. Variantele Optimizate local) și a genera rapoartele finale, rulați comanda:
```bash
python main_pipeline.py
```

### 2. Rularea Optimizării Hiperparametrilor (Optuna)
Pentru a efectua strict tuning-ul hiperparametrilor și a stoca mediul de testare al fiecărui model folosind logica de evitare a data leakage-ului (Time-Series Cross Validation), executați:
```bash
python run_optuna_optimization.py
```

---

## 📂 Salvarea Rezultatelor și Rapoartelor

Aplicația este construită cu o arhitectură non-distructivă. Astfel:
- **Rapoartele generale** (de comparație, performanță RMSE, MAPE etc.) sunt stocate în directorul:  
  `outputs/reports/`
- **Studiile izolate Optuna** (în format baze de date SQLite, pregătite pentru Dashboard) sunt stocate în directorul dedicat:  
  `outputs/optuna_studies/`

---

## 📈 Vizualizarea Studiilor în Optuna Dashboard

Baza proiectului suportă lansarea unui panou de control vizual prin `optuna-dashboard`.  
Pentru a porni vizualizarea interactivă:
1. Deschideți fișierul **`pornire_dashboard_optuna.ipynb`** folosind un editor suportat (ex: JupyterLab, VS Code).
2. Rulați celula aferentă modelului pe care doriți să îl inspectați (XGBoost pe port 7771, SARIMA pe 7772, Prophet pe 7773).
3. Dashboard-ul va deveni disponibil automat în browser la adresa **localhost** urmată de portul respectiv (ex: `http://localhost:7771`).

---

## ⚠️ Observație privind Fișierele de Model (.joblib)

Am decis **să nu includem fișierele binare `.joblib`** (modelele pre-antrenate) în depozitul / arhiva acestui cod sursă.  
**Motivul:** Aceste fișiere pot depăși limita de dimensiune acceptată pentru predare sau repository (din cauza ansamblurilor ample sau a limitărilor de arhitectură ale XGBoost/SARIMA). Validitatea și succesul antrenamentelor sunt demonstrate cu fermitate prin structura detaliată a tabelelor din folderul `outputs/reports/` și în special de baza de date cu istoric a încercărilor `outputs/optuna_studies/`. Re-generarea modelelor necesită doar reluarea pasului 1 din secțiunea „Ghid de Rulare”.
