# Scop

- Adăugarea unui chatbot bazat pe un model LLM, care să răspundă la întrebări despre cursul valutar GBP/RON.
- Chatbot-ul trebuie să poată folosi funcțiile aplicației ca tool-uri, prin apelarea endpoint-urilor existente din backend-ul FastAPI.
- Scopul final este ca utilizatorul să poată întreba natural despre cursuri, prognoze, modele, metrici, Optuna și actualizarea datelor.

# Context

- Aplicația este construită full-stack:
  - backend cu FastAPI;
  - frontend cu Streamlit;
  - bază de date SQLite;
  - pipeline ML pentru prognoza cursului GBP/RON.
- Backend-ul rulează local prin:

```bash
python run_api.py