import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import sys
import os
from typing import Optional, Dict, Any

# Importuri din pachetul curs_bnr
from curs_bnr.config import CSV_PATH

# Setările principale
URL = "https://www.cursbnr.ro/curs-valutar-bnr"

# Request aprobat: Verificat ca cerere POST tipică de manipulare formular a BNR
PAYLOAD = {
    "currency": "GBP",
    "dataStart": "22/02/2020",
    "dataEnd": "19/03/2026"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def curata_valoare(text: str) -> Optional[float]:
    """
    Curăță valoarea cursului valutar dintr-un string HTML 
    și o convertește într-un tip de date float.
    """
    try:
        partea_numerica = text.strip().split()[0]
        partea_numerica = partea_numerica.replace(",", ".")
        return float(partea_numerica)
    except (ValueError, IndexError):
        return None

def curata_data(text: str) -> Optional[str]:
    """
    Formatează data calendaristică preluată de pe site-ul BNR 
    într-un format standardizat YYYY-MM-DD.
    """
    try:
        data_clean = text.strip().replace(".", "/")
        dt_obj = datetime.strptime(data_clean, "%d/%m/%Y")
        return dt_obj.strftime("%Y-%m-%d")
    except ValueError:
        return None

def parse_table_rows(table_element: Any, date_unice: Dict[str, float]) -> None:
    """
    Extrage datele din tabel și le stochează în dicționar fără coliziuni de dedublare.
    """
    tbody = table_element.find("tbody")
    rows = tbody.find_all("tr") if tbody else table_element.find_all("tr")
    
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            data_formatata = curata_data(cols[0].text)
            valoare_formatata = curata_valoare(cols[1].text)
            
            if data_formatata and valoare_formatata:
                # [DEDUPLICARE] Eliminăm potențialele duplicate folosind data pe post de cheie.
                # Dacă aceeași dată apare de mai multe ori pe parcurs, va fi suprascrisă.
                date_unice[data_formatata] = valoare_formatata

def run_scraper(output_file: str = str(CSV_PATH)) -> None:
    """
    Orchestrează extragerea cursului de pe cursbnr.ro, incluzând paginarea 
    și salvarea finală a datelor curățate și sortate în format CSV.
    """
    print(f"Incepem extragerea pentru limitele {PAYLOAD['dataStart']} - {PAYLOAD['dataEnd']}...")
    sess = requests.Session()
    
    # [DEDUPLICARE] Inițializăm un dicționar. Structura evită repetarea automată a aceleiași zile.
    date_unice = {}
    
    try:
        # Metoda aprobată curentă - acțiune specifică formularelor HTML (POST form data)
        response = sess.post(URL, data=PAYLOAD, headers=HEADERS)
        if response.status_code != 200:
            print(f"Eroare severa la initiere: cod HTTP {response.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
         print(f"Eroare de retea/conexiune: {e}")
         sys.exit(1)
         
    soup = BeautifulSoup(response.text, "html.parser")
    tabel_principal = soup.find("table", {"id": "table-currencies"})
    
    if not tabel_principal:
        print("Eroare logica: Tabelul de extragere lipseste complet. Raspuns suspect.")
        sys.exit(1)
        
    parse_table_rows(tabel_principal, date_unice)
    
    # [PAGINARE CONDIȚIONALĂ] Scriptul detectează paginarea și rulează requestul doar DACĂ găsește buton "next".
    pagina_curenta = 1
    bucla_paginare = True
    
    while bucla_paginare:
        pagination_container = soup.find("ul", class_="pagination")
        bucla_paginare = False
        
        if pagination_container:
            legaturi = pagination_container.find_all("a")
            for leg in legaturi:
                if "»" in leg.text or "Next" in leg.text or leg.get('rel') == ['next']:
                    next_url = leg.get("href")
                    if next_url:
                        if not next_url.startswith("http"):
                            next_url = "https://www.cursbnr.ro" + next_url
                        
                        pagina_curenta += 1
                        print(f"Se detecteaza paginare! Trecem la elementul {pagina_curenta}...")
                        
                        try:
                            # Cerere de pagină nouă pe baza linkului de paginare identificat valid
                            resp_next = sess.get(next_url, headers=HEADERS)
                            if resp_next.status_code == 200:
                                soup = BeautifulSoup(resp_next.text, "html.parser")
                                tb_next = soup.find("table", {"id": "table-currencies"})
                                if tb_next:
                                    parse_table_rows(tb_next, date_unice)
                                    bucla_paginare = True 
                                    break 
                        except Exception as e:
                            print(f"[!] Atentie: Preluarea paginii a esuat prematur la indice {pagina_curenta}: {e}")
                            bucla_paginare = False
                            
    if not date_unice:
        print("Extractia datelor nu a produs rezultate.")
        sys.exit(1)
        
    # [SORTARE] Sortăm cronologic din vechi în nou.
    date_sortate = sorted(date_unice.items(), key=lambda x: x[0])
    
    # Asigurăm existența folderului părinte
    parent_dir = os.path.dirname(os.path.abspath(output_file))
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    try:
        with open(output_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            
            # Aplicăm antetul fix aprobat de utilizator
            writer.writerow(["date", "gbp_rate"])
            
            # Inserăm datele pre-curățate și unice direct spre document
            for d_str, v_float in date_sortate:
                writer.writerow([d_str, v_float])
                
        print(f"\n[SUCCESS] Finalizare! Am gasit {len(date_sortate)} rate unice pentru GBP.\nFisier salvat -> {output_file}.")
    except OSError as csv_err:
        print(f"Eroare neplacuta la scrierea CSV: {csv_err}")

def main() -> None:
    run_scraper()

if __name__ == "__main__":
    main()
