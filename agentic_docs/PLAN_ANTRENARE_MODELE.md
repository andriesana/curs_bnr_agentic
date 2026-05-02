# PLAN_ANTRENARE_MODELE.md
## Arhitectura Sistemului de Prognoză pentru Cursul de Schimb (BNR)

Acest document definește planul complet de preprocesare, validare, și evaluare al unui sistem de Machine Learning conceput să prognozeze cursul valutar GBP la orizont de o zi (T+1).

---

### 1. Definirea celor 3 modele selectate
1. **Modelul ARIMA/SARIMA (AutoRegressive Integrated Moving Average):**
   - *Rol:* Acționează ca instrument clasic și model de baseline. 
   - *Explicație:* Captează eficient dinamica liniară de corelație cu trecutul raportată la tendința curentă a zgomotului statistic.
2. **Modelul XGBoost (eXtreme Gradient Boosting):**
   - *Rol:* Abordare ultra-rapidă și robustă non-liniară, optimizată cu arbori de decizie complecși.
   - *Explicație:* Nu recunoaște datele native de "timp", dar interacționează minunat cu Feature Engineering (lag-uri, decupări).
3. **Modelul Facebook Prophet:**
   - *Rol:* Oferă soliditate majoră pe fluctuațiile tipice de business și rezonează perfect cu serii de timp cu structură neuniformă.
   - *Explicație:* Construit să descompună intrările în trend continuu alăturat de efectele sezonalității complexe umane.

### 2. Preprocesarea și Tratarea Gap-urilor Temporale
1. **Re-Eșantionarea (`Resampling`):** Timpul convertit în index datat `DatetimeIndex` se expune uniform, zi de zi (`freq='D'`).
2. **Rezolvarea datelor lipsă (`Imputation`):** Pentru golurile din weekend și de sărbătorile legale, utilizăm tehnica **Forward-Fill (`.ffill()`)**. Orice curs dintr-o Vineri suplini logic golul Sâmbătă și Duminică.
3. **Feature Engineering (Special pentru XGBoost):** Crearea unei mașini formale de variabile ajutătoare.
   - *Lags (întârzieri):* Valoarea GBP în urmă cu 1 zi, 3 zile, sau 7 zile.
   - *Medii Mobile Explicite (Rolling Stats):* Includerea și listarea directă a valorilor derivate dintro medie tehnică pur fixativă prin reținerea explicită a **Mediei Mobile de 7 zile** și a **Mediei Mobile de 14 zile**, extrăgând forjat ritmul pieții la nivel imediat apropiat/mediu.

### 3. Delimitarea Seturilor (Testul Izolat)
- **Setul Restrâns de Test Final (Păstrat Izolat):** O abordare absolut obiectivă preia exclusiv ultimele **14 zile cronologice** din flux și le ascunde sistemului. O numim fereastra de Validare Externă absolută (Hold-out Test).
- **Setul de Antrenament Extins:** Orice alte date mai vechi de aceste 14 zile alcătuiește Setul de Antrenare complet, unde și Cross-Validation-ul, și alegerea parametrilor operează strict izolat aici.

### 4. Validarea Încrucișată pe Setul de Antrenament (Time-Series CV)
Pe datele ce formează "Setul de antrenament", validăm cu **Rolling Window Cross-Validation** (ex. `TimeSeriesSplit` din familiile de tooluri):
- Se divide totul in subseturi succesive temporale. Sistemul antrenează o fereastră extinsă (ex. anii 2020-2022) și testează pe fereastra imediat ulterioară, mereu cronologic. La fiecare iterare se lărgește contextul vizionând fix înainte. Ne apărăm clar viitorul de trecut (Data Leakage evitat perfect).

### 5. Plan de modificare pentru optimizarea hiperparametrilor

Această secțiune detaliază strategiile de tuning pentru cele trei modele selectate, utilizând două abordări distincte pentru a identifica configurația optimă pe setul de antrenament. Optimizarea se face folosind **Time-Series Cross Validation** (pentru a respecta cronologia datelor), iar metrica principală de decizie pentru alegerea setului „câștigător” este **RMSE (Root Mean Square Error)**.

#### Varianta 1: GridSearch (Căutare Exhaustivă)
GridSearch explorează sistematic toate combinațiile posibile dintr-o grilă predefinită de valori discrete. Este utilă pentru spații de căutare bine delimitate și pentru modele unde parametrii sunt preponderent întregi sau categorici.

1. **Modelul SARIMA:**
   - **Hiperparametri optimizați:** `order (p, d, q)` și `seasonal_order (P, D, Q, s)`.
   - **Tuning:** Se extinde spațiul de căutare pentru `p` și `q` între [0, 3], `d` [0, 1], iar pentru partea sezonieră `P, Q` între [0, 2] și `D` [0, 1] cu `s=7`.
   - **Utilitate:** Permite o mapare completă a interacțiunilor dintre termenii autoregresivi și media mobilă în contextul sezonalității săptămânale.

2. **Modelul XGBoost:**
   - **Hiperparametri optimizați:** `eta` (learning rate), `gamma`, `subsample`, `n_estimators`, `max_depth`.
   - **Tuning în GridSearch:** Se utilizează grile fixe:
     - `eta`: [0.01, 0.05, 0.1]
     - `gamma`: [0, 0.1, 0.2]
     - `subsample`: [0.7, 0.8, 0.9]
     - `n_estimators`: [50, 100, 200]
     - `max_depth`: [4, 5, 6]
   - **Features:** Se includ obligatoriu mediile mobile calculate anterior: `ma_7` (Media Mobilă 7 zile) și `ma_14` (Media Mobilă 14 zile).
   - **Utilitate:** Asigură testarea unor praguri de complexitate controlate pentru a evita overfitting-ul pe serii scurte.

3. **Modelul Facebook Prophet:**
   - **Hiperparametri optimizați:** `changepoint_prior_scale`, `seasonality_prior_scale`, `seasonality_mode`.
   - **Tuning în GridSearch:** Se iterează prin liste discrete (ex: `changepoint_prior_scale`: [0.001, 0.01, 0.1]).
   - **Utilitate:** Verifică stabilitatea modelului pe configurații de bază documentate.

#### Varianta 2: Optuna (Optimizare Bayesiană)
Optuna utilizează algoritmi de probabilitate (precum TPE - Tree-structured Parzen Estimator) pentru a învăța din iterațiile anterioare și a ghida căutarea către zonele cele mai promițătoare din spațiul hiperparametrilor.

1. **Modelul SARIMA:**
   - **Tuning în Optuna:** Parametrii `p, d, q, P, D, Q` sunt sugerați ca întregi (`trial.suggest_int`) într-un interval extins.
   - **Utilitate:** Eficientă când numărul total de combinații devine prea mare pentru un GridSearch clasic, permițând explorarea unor ordine superioare fără cost computațional prohibitiv.

2. **Modelul XGBoost:**
   - **Hiperparametri optimizați:** Aceleași variabile (`eta, gamma, subsample, n_estimators, max_depth`).
   - **Tuning în Optuna:** Parametrii precum `eta` sau `gamma` sunt explorați în intervale continue (`trial.suggest_float`), permițând găsirea unor valori „fine” (ex: 0.035 în loc de pragul fix 0.05).
   - **Utilitate:** Identifică echilibrul optim între capacitatea de învățare (eta) și regularizare (gamma) mult mai rapid decât o grilă fixă.

3. **Modelul Facebook Prophet:**
   - **Hiperparametri optimizați:** `changepoint_prior_scale`, `seasonality_prior_scale`, `seasonality_mode`.
   - **Tuning în Optuna:** Se explorează scalele de prioritate în intervale logaritmice.
   - **Utilitate:** Prophet beneficiază enorm de Optuna deoarece scalele de prioritate sunt parametri continui sensibili la ordinul de mărime.

Aștept aprobarea pentru implementarea acestui plan de optimizare.

### 6. Stabilirea Metricilor și Zona Raportărilor Specifice
Utilizăm metrici predefinte (`MAE`, `RMSE`, `MAPE`). Repartiția pe care le fixam diferă strategic:
1. **Pe Validarea Încrucișată (CV-ul Setului de Train intern):**
   - Raportăm **media scorului pe metrici generalizate dintr-un algoritm validat (Scorurile de Cross-Validare)**. Aici RMSE, MAE din cele K folduri acționează strict la alegerea invingătorului arhitecturii si tuning-ului de la pct. 5, raportând *Media Evaluărilor Multiple cronologice interne*.
2. **Pe Testul Final (Rezerva finală vizând ultimele 14 Zile):**
   - Acționează judecătorul "MAPE final curat" / "RMSE test out-of-bag". Va calcula exclusiv calibrarea pe care modelul gata-antrenat ce tocmai a învins din tuning, o asuma pe diferența exactă pe zile dintre Cursul Adevărat produs de piață și Estimările predictivului lansate oarb. E metrica reală expusă la stakeholder.

### 7. Intervalele de Încredere Oficializate (Confidence Intervals la 95%) pe toate Metodele
Proiecția fiecărui model la ziua următoare produce inclusiv benzile decizionale ale predictibilității superioare/inferioare:
- **SARIMA:** Deduce empiric și parametric aceste incertitudini luând matematic ecuațiile de tip covarianță din logica reziduurilor pe precesul auto-regresiv intern, apeland direct derivatele de funcții bază: `get_forecast().conf_int()`.
- **Prophet (Meta):** Furnizat nativ extrem de agil utilizând metoda complet non-lineara cu inferențe MCMC (lanțuri iterative Markov Monte-Carlo de vizualizari din distribuție) producătoare a extremelor `yhat_lower`/`yhat_upper`.
- **XGBoost:** Varianta brută regresează „o singură direcție netă”. Va accesa conceptul de *Quantile Regression* obiectiv-dedicat ce invață modelul să minimizeze funcțiile de eroare prin forțarea așezării a două sub-predicții strict modelate separat pe quantile absolute marginare: Inferior vizat pe prag de Quantila alfa `5%` iar Superior țintind strict pe capăt invers Alpha la  `95%` simulând asfel un pseudo interval de încredere asamblat matematic pur iterativ.

### 8. Salvarea celui mai bun model
Validarea adunată total la pct.6 reține un Rege per overall final. Modelul va acoperi întreg pipeline-ul creat pe Feature Engineering si logica parametrizanta și va persista standard un pre-încărcat în CWD local tipic arhivarii Python utilizator: `predictiv_model_gbp_bnr.pkl` sau implementarea prin librăria robustă de i/o paralela `joblib`.

### 9. Vizualizarea grafică Plotly Interactivă
Librăria `Plotly` coordonează compararea previziunii finale.
- Va desena o traiectorie duală asimetrică formată clar printr-un afișaj general care conturează Axa Oficială T+1/T+14 Zile (Actual) trasată paralel de predictivul abstract derivat pe aceași zonă pur vizionară. 
- Umbrirea/Umbra tip translucid fin definită fixând margini de predictabilitate aduce vizionar tot fenomenul estimativ la preț de decizie rapidă din capul intervalelor trasate logic superior. Beneficiază agil pe un element tip „Range Slider Selector” pentru detunare vizuală a analizei spre micro/macro decizie live pe element web integrat minimal.
