# Conceptul de Tool Calling (Funcții Locale) în Agentul BNR

Acest document explică modul în care o funcție Python locală poate fi utilizată ca "tool" (instrument) de către un model de limbaj (LLM), cum este Gemini, pentru a interacționa cu sistemul local.

## Cum funcționează?

Mecanismul de Tool Calling permite modelului să "decidă" singur când are nevoie de informații externe sau de execuția unor acțiuni pe care el nu le poate face singur (de exemplu, accesarea unei baze de date sau a unui API local).

În implementarea din `src/curs_bnr/model_utils.py`, fluxul este următorul:

1.  **Definirea funcției locale**: Orice funcție Python care returnează un rezultat poate deveni un tool. Exemplu: `get_latest_exchange_rate()`.
2.  **Descrierea (Schema)**: Modelul nu vede codul sursă al funcției, ci o descriere JSON. Aceasta se definește în `TOOLS_SCHEMA`, unde îi specificăm modelului:
    *   **Ce face funcția** (descriere textuală).
    *   **Ce parametri acceptă** (tipuri de date, obligativitate).
3.  **Înregistrarea**: În `TOOL_REGISTRY`, mapăm numele tool-ului pe care îl vede modelul cu funcția reală din Python.
4.  **Bucla Agentică (Loop)**:
    *   Utilizatorul pune o întrebare.
    *   Dacă modelul decide că are nevoie de date, acesta nu răspunde cu text, ci cu un obiect de tip `FunctionCall`.
    *   Codul local (executorul) interceptează acest apel, execută funcția Python reală și obține rezultatul.
    *   Rezultatul este trimis înapoi la model sub formă de `FunctionResponse`.
    *   Modelul analizează datele primite și formulează răspunsul final în limbaj natural.

## Pași pentru adăugarea unui tool nou

Dacă dorești să extinzi capacitățile agentului, urmează acești pași în `model_utils.py`:

1.  **Creează funcția Python**: Scrie logica de care ai nevoie.
2.  **Definește schema**: Adaugă un nou obiect în lista `TOOLS_SCHEMA`. Asigură-te că descrierea este foarte explicită, deoarece este singurul indiciu pe care modelul îl are pentru a decide apelarea.
3.  **Înregistrează funcția**: Adaugă intrarea corespunzătoare în dicționarul `TOOL_REGISTRY`.

## Concluzie

Prin acest mecanism, agentul devine capabil să interacționeze dinamic cu datele reale ale aplicației `curs_bnr_agentic`, fără ca dezvoltatorul să trebuiască să scrie logică condițională complexă pentru fiecare tip de întrebare. Modelul "înțelege" scopul fiecărui tool și îl folosește doar atunci când este necesar pentru a rezolva sarcina primită.
