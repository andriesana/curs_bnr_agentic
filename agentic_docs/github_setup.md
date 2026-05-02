# Ghid de Configurare GitHub

Acest document descrie pașii necesari pentru publicarea proiectului de prognoză a cursului valutar BNR pe o platformă precum GitHub.

## Pași pentru Publicare

1. **Verificare Git instalat**
   Asigură-te că utilitarul Git este instalat pe sistemul tău. Poți verifica deschizând terminalul și rulând:
   ```bash
   git --version
   ```

2. **Inițializare repository local**
   Navighează în folderul rădăcină al proiectului (`Tema 3`) și inițializează un repository Git gol:
   ```bash
   git init
   ```

3. **Adăugarea fișierelor în stagiul de versionare**
   Include toate fișierele (cu excepția celor ignorate prin `.gitignore`) pentru primul commit:
   ```bash
   git add .
   ```

4. **Crearea primului commit**
   Salvează stadiul curent al codului printr-un mesaj descriptiv:
   ```bash
   git commit -m "Initial commit - BNR exchange rate optimization pipeline"
   ```

5. **Creare repository pe GitHub**
   Accesează [GitHub](https://github.com/), autentifică-te, creează un repository nou (gol) și copiază adresa URL generată.

6. **Conectarea repository-ului local cu cel de la distanță (remote)**
   Înlocuiește `URL_REPOSITORY` cu adresa copiată de pe platforma web:
   ```bash
   git remote add origin URL_REPOSITORY
   ```

7. **Setarea branch-ului principal**
   Asigură-te că branch-ul principal se numește standard `main`:
   ```bash
   git branch -M main
   ```

8. **Trimiterea codului (Push)**
   Urcă toate modificările pe GitHub, setând totodată și branch-ul implicit (upstream):
   ```bash
   git push -u origin main
   ```

---

## ⚠️ Gestionarea Fișierelor Mari

Este foarte important de reținut:
- Modelele de format **`.joblib`** și **`.pkl`** **nu se urcă în repository**, deoarece pot depăși limita standard de dimensiune per fișier impusă de GitHub. În plus, stocarea binarelor greoaie încarcă inutil istoricul Git.
- Aceste modele **se pot regenera extrem de ușor** local prin simpla rulare a pipeline-ului matematic agreat (`python main_pipeline.py`). 
- Dacă versionarea repetată și stocarea strictă a acestor binare masive devine o cerință indispensabilă de lucru în echipă, se recomandă utilizarea extensiei dedicate [Git LFS (Large File Storage)](https://git-lfs.github.com/).
