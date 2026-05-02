# PLAN_IMPLEMENTARE_SCRAPER.md

## 1. Planul tehnic revizuit: Scraping Curs BNR (GBP)

Acest document descrie la nivel de arhitectură și proces logic pașii necesari pentru construcția scraper-ului de date pentru site-ul `cursbnr.ro`, cu accent pe siguranța extracției și validărilor.

### Obiectiv
Extragerea cursului valutar de schimb al BNR între limitele temporale `22/02/2020` și `19/03/2026` pentru `GBP` și salvarea rezultatului, curățat și formatat, într-un fișier local `gbp_curs_bnr.csv`.

---

## 2. Detalii riguroase impuse

### A. Verificarea încărcării datelor (Dinamic vs. Static)
1. **Procedură:** Vom accesa DevTools din browser (F12) pe tab-ul *Network*. Vom completa manual formularul de filtrare pe site (Monedă, Data de început, Data de final) și vom declanșa căutarea.
2. **Evaluarea cererii principale (Type: Document):** Analizăm primul request/răspuns înregistrat (sau pagina unde are loc redirecționarea). Tab-ul *Preview* sau *Response* identifică clar codul primit de la server.
3. **Decizia:**
   - *Static (Server-Side Rendered):* Nodul `<table id="table-currencies">` și rândurile de date aferente (sub formă de blocuri de text `<tr>`) se regăsesc fizic în răspunsul direct `Document` al cererii POST/GET de formular. Aici se aplică metoda clasică `requests` + `BeautifulSoup`.
   - *Dinamic (API / XHR):* Răspunsul Document nu conține tabelul, iar tabelul este prelucrat ulterior folosind Javascript via fetch/XHR (cu un răspuns cel mai adesea de tip JSON sau un fragment de HTML primit ulterior).

### B. Parametrii exacți ale cererii
Din analiza câmpurilor date, request-ul (probabil de tip POST sub encriptarea `application/x-www-form-urlencoded` adiacent acțiunii formularului) va trebui să trimită pe corpul mesajului (`data=...` în `requests`) cel puțin următoarele chei și valori asociate:
- `currency`: `"GBP"`
- `dataStart`: `"22/02/2020"` sau echivalent conform formatului cerut de input.
- `dataEnd`: `"19/03/2026"`
- (Alături de posibili tokeni CSRF secreți dacă sunt puși în evidență ca *hidden inputs* în pre-verificarea structurii formularului generat).

Dacă este un request asincron de tip form (`GET`), parametrii se pasează sub formă de query string. Parametrii se trimit cu `params={"currency": "GBP", "dataStart": "22/02/2020", "dataEnd": "19/03/2026"}`.

### C. Paginarea (Detectare și procesare)
1. **Detectarea prezenței paginării:** Vom căuta, tot prin `BeautifulSoup`, prezența unui container de paginare sub tabelul extras (ex. `<ul class="pagination">`).
2. **Identificarea logică:** Se identifică hiperlink-ul care desemnează butonul „Următoarea Pagină” (Next) (ex. `<a href="?page=2" ...>`).
3. **Procesarea iterativă:**
   - La fiecare buclă de iterație (`while True`), script-ul așteaptă parsarea unui tabel.
   - La final de document curent, interoghează existența butonului de paginare.
   - Dacă obiectul returnat de selector nu este `None`, extragem parțial/în totalitate atributul `href` (URL-ul relativ/absolut) și re-declanșăm cererea pe linkul găsit.
   - Când funcția de identificare a butonului `Next` dă greș (ultima pagină), bucla `while` se oprește (`break`).

### D. Tratarea tabelului lipsă sau a răspunsului gol
1. Dacă `soup.find('table', {'id': 'table-currencies'})` este evaluat ca egal cu `None`, o excepție controlată (`ValueError` sau un log critic) este aruncată, atenționând utilizatorul de imposibilitate extragerii - scriptul va relata eroarea și se va întrerupe prematur.
2. Erori uzuale gestionate:
   - Apel restricționat din motive tip „Rate-limit”, răspuns cu soft `captcha`: verificarea statusului HTTP. Orice cod care diferă de `<200 OK>` înseamnă oprire bruscă asumată de script.
   - Tabel structurat însă fără un tag `<tbody>` sau tag `tr` efectiv în acesta: înseamnă că data respectivă specifică o absență de validare ori intervalul nu înregistrează valori. Ignorăm (logăm lipsa datelor) sau închidem script-ul lin.

### E. Formatul datelor salvate în fișier (CSV)
Fișierul `gbp_curs_bnr.csv` va dispune de separarea simplă tip `,` având următoarele aspecte detaliate:
- **Structura antet:** Două coloane, declarate inițial pe rând 1: `Data,Valoare` (unde *Data* e ziua afișată curent și *Valoare* prețul ronului estimat pentru 1 GBP).
- **Consistență pe rânduri:** Set de date standard - exemplu: `2020-02-22,5.2934`.

### F. Tratamentul riguros al conversiilor (Numeric și Date time)
1. **Curățarea celulelor de tip Monedă/Valoare:**
   - Fie string-ul obținut: `"5,2934 RON (simbol procentual +/-)"`.
   - Modificare structurală: Vom decupa (`split()[0]` sau RegEx) de extragerea exclusivă referitoare la număr.
   - Vom utiliza înlocuirea din virgulă în punct (european->US): ex. `val = string.replace(',', '.')`.
   - Tipe-casting forțat într-un float real: `try: val_curenta = float(val) except ValueError: ....`.
2. **Curățarea celulelor pentru dată (`Date`):** 
   - Fie string-ul obținut: `"22.02.2020"` sau `"22/02/2020"`.
   - Utilizăm librăria `datetime` a Python.
   - Parcurgem la obiect folosind formatul adecvat: `data_obj = datetime.strptime(data_string.strip(), "%d/%m/%Y")` (sau ajustat din observare directă în consolă).
   - Conversia în final către CSV folosește formatul ISO internațional (anul prioritar): `data_finala = data_obj.strftime("%Y-%m-%d")`.
   - Conversia riguroasă a datelor previne probleme ale formatării in Excel unde 01/02 poate echivala 2 Ianuarie în loc de 1 Februarie.
