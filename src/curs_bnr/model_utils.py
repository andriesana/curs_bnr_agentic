"""
model_utils.py – Agent Curs BNR GBP/RON cu Tool Calling local

Demonstrează cum funcții Python locale pot fi înregistrate ca
"tool-uri" pe care modelul Gemini le poate apela automat atunci când
are nevoie de date din aplicația curs_bnr_agentic.

Flux agentic (ReAct-style):
  1. Utilizatorul trimite un mesaj natural (ex: "Care este ultimul curs GBP/RON?")
  2. Modelul decide -> emite un FunctionCall (nu text direct)
  3. Codul local execută funcția corespunzătoare
  4. Rezultatul este trimis înapoi ca FunctionResponse
  5. Modelul formulează răspunsul final în limbaj natural

Pașii 2-4 se repetă până când modelul nu mai cere niciun tool.

Rulare rapidă (demo):
    $env:PYTHONPATH = "src"
    python -m curs_bnr.model_utils

Setare cheie API:
    $env:GEMINI_API_KEY = "cheia_ta"   # PowerShell
    export GEMINI_API_KEY="cheia_ta"   # bash

Important:
    Backend-ul FastAPI trebuie pornit înainte:
        python run_api.py

    API-ul proiectului rulează implicit pe:
        http://localhost:8000
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable

import requests

# ── Configurare ──────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BNR_BACKEND_URL", "http://localhost:8000")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


# ═════════════════════════════════════════════════════════════════════════════
# SECȚIUNEA 1: Funcțiile locale (viitoarele "tools")
# Aceste funcții pot apela API-ul local FastAPI al proiectului.
# ═════════════════════════════════════════════════════════════════════════════

def get_latest_exchange_rate() -> dict[str, Any]:
    """
    Returnează cel mai recent curs GBP/RON disponibil prin API.

    Tool folosit când utilizatorul întreabă despre cursul curent,
    ultimul curs disponibil sau valoarea recentă GBP/RON.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/api/rates", timeout=10)
        response.raise_for_status()
        rates = response.json()

        if not rates:
            return {"success": False, "error": "Nu există date de curs disponibile."}

        latest = rates[-1]

        return {
            "success": True,
            "date": latest.get("date"),
            "value": latest.get("value") or latest.get("gbp_rate") or latest.get("rate"),
            "currency": "GBP/RON",
            "source": "/api/rates",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "hint": "Verifică dacă backend-ul este pornit cu: python run_api.py",
        }


def get_exchange_rates() -> dict[str, Any]:
    """
    Returnează istoricul cursului GBP/RON.

    Tool folosit când utilizatorul cere evoluția cursului,
    istoricul valorilor sau datele disponibile.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/api/rates", timeout=10)
        response.raise_for_status()
        rates = response.json()

        return {
            "success": True,
            "currency": "GBP/RON",
            "count": len(rates),
            "rates_preview": rates[-10:] if len(rates) > 10 else rates,
            "source": "/api/rates",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "hint": "Verifică dacă backend-ul este pornit cu: python run_api.py",
        }


def get_forecast_summary() -> dict[str, Any]:
    """
    Returnează rezumatul prognozei curente și modelul câștigător.

    Tool folosit când utilizatorul întreabă despre prognoză,
    modelul câștigător, RMSE-ul celui mai bun model sau statusul sistemului.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/api/forecast/latest", timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            return {"success": False, "error": "Nu există prognoză disponibilă."}

        return {
            "success": True,
            "currency": "GBP/RON",
            "winner_model": (
                data.get("winner_model")
                or data.get("model_castigator")
                or data.get("best_model")
                or data.get("model")
            ),
            "rmse_best_model": (
                data.get("rmse")
                or data.get("best_rmse")
                or data.get("rmse_best_model")
            ),
            "mae": data.get("mae"),
            "mape": data.get("mape"),
            "latest_date": data.get("latest_date") or data.get("date"),
            "latest_value": data.get("latest_value") or data.get("value"),
            "status": data.get("status"),
            "raw_response": data,
            "source": "/api/forecast/latest",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "hint": "Verifică dacă backend-ul este pornit cu: python run_api.py",
        }


def get_model_metrics() -> dict[str, Any]:
    """
    Returnează metricile modelelor SARIMA, Prophet și XGBoost.

    Tool folosit când utilizatorul cere comparația modelelor,
    performanța modelului câștigător sau metrici precum RMSE/MAPE.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/api/metrics", timeout=10)
        response.raise_for_status()
        metrics = response.json()

        if not metrics:
            return {"success": False, "error": "Nu există metrici disponibile."}

        rows = metrics
        if isinstance(metrics, dict):
            rows = metrics.get("metrics") or metrics.get("data") or metrics.get("rows") or []

        if not isinstance(rows, list):
            return {
                "success": False,
                "error": "Format neașteptat pentru răspunsul /api/metrics.",
                "raw_response": metrics,
            }

        def get_rmse(row: dict[str, Any]) -> float:
            value = row.get("RMSE", row.get("rmse", float("inf")))
            try:
                return float(value)
            except (TypeError, ValueError):
                return float("inf")

        sorted_rows = sorted(rows, key=get_rmse)
        best_row = sorted_rows[0] if sorted_rows else {}

        model_name = best_row.get("Model") or best_row.get("model") or best_row.get("model_name")
        variant = best_row.get("Variant") or best_row.get("variant")

        if model_name and variant:
            winner = f"{model_name} ({variant})"
        else:
            winner = model_name or "N/A"

        return {
            "success": True,
            "currency": "GBP/RON",
            "winner": winner,
            "best_rmse": get_rmse(best_row) if best_row else None,
            "models": sorted_rows,
            "source": "/api/metrics",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "hint": "Verifică dacă backend-ul este pornit cu: python run_api.py",
        }


def get_training_runs() -> dict[str, Any]:
    """
    Returnează istoricul rulărilor de antrenare din aplicație.

    Tool folosit când utilizatorul întreabă despre ultima rulare,
    istoricul antrenărilor sau statusul antrenării.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/api/runs", timeout=10)
        response.raise_for_status()
        runs = response.json()

        return {
            "success": True,
            "count": len(runs) if isinstance(runs, list) else None,
            "runs": runs,
            "source": "/api/runs",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "hint": "Verifică dacă backend-ul este pornit cu: python run_api.py",
        }


def get_optuna_links() -> dict[str, Any]:
    """
    Returnează informații despre dashboard-urile Optuna.

    Tool folosit când utilizatorul întreabă cum se deschid studiile Optuna,
    ce porturi se folosesc sau unde sunt bazele de date SQLite.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/api/optuna-links", timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "optuna": data,
            "note": (
                "Dashboard-urile Optuna trebuie pornite separat din terminal "
                "înainte de accesarea linkurilor localhost."
            ),
            "source": "/api/optuna-links",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "hint": "Verifică dacă backend-ul este pornit cu: python run_api.py",
        }


def trigger_scrape() -> dict[str, Any]:
    """
    Declanșează sau descrie actualizarea datelor BNR prin API.

    Tool folosit când utilizatorul cere actualizarea datelor istorice.
    În proiectul actual, endpoint-ul poate funcționa ca mecanism sigur
    care explică modul de rulare a scraperului.
    """
    try:
        response = requests.post(f"{BACKEND_URL}/api/scrape", timeout=60)
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "message": data.get("message", "Cererea de actualizare a datelor a fost trimisă."),
            "raw_response": data,
            "source": "/api/scrape",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "hint": "Verifică dacă backend-ul este pornit cu: python run_api.py",
        }


def trigger_train() -> dict[str, Any]:
    """
    Returnează instrucțiuni pentru reantrenarea modelelor.

    Tool folosit când utilizatorul cere reantrenarea modelelor.
    Nu pornește direct pipeline-ul complet, pentru a evita blocarea aplicației.
    """
    try:
        response = requests.post(f"{BACKEND_URL}/api/train", timeout=30)
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "message": data.get(
                "message",
                "Pentru reantrenare completă rulează în terminal: python main_pipeline.py",
            ),
            "raw_response": data,
            "source": "/api/train",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "hint": "Verifică dacă backend-ul este pornit cu: python run_api.py",
        }


# ═════════════════════════════════════════════════════════════════════════════
# SECȚIUNEA 2: Registrul de tools
# Mapare nume_tool → funcție locală + schemă pentru model
# ═════════════════════════════════════════════════════════════════════════════

TOOL_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
    "get_latest_exchange_rate": get_latest_exchange_rate,
    "get_exchange_rates": get_exchange_rates,
    "get_forecast_summary": get_forecast_summary,
    "get_model_metrics": get_model_metrics,
    "get_training_runs": get_training_runs,
    "get_optuna_links": get_optuna_links,
    "trigger_scrape": trigger_scrape,
    "trigger_train": trigger_train,
}

TOOLS_SCHEMA = [
    {
        "name": "get_latest_exchange_rate",
        "description": (
            "Returnează cel mai recent curs GBP/RON disponibil în aplicație. "
            "Folosește acest tool când utilizatorul întreabă despre cursul curent, "
            "ultimul curs disponibil sau valoarea recentă GBP/RON."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_exchange_rates",
        "description": (
            "Returnează istoricul cursului GBP/RON. "
            "Folosește acest tool când utilizatorul întreabă despre evoluția cursului "
            "sau istoricul valorilor."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_forecast_summary",
        "description": (
            "Returnează prognoza curentă pentru GBP/RON, modelul câștigător "
            "și metricile relevante dacă sunt disponibile. "
            "Folosește acest tool când utilizatorul întreabă despre prognoze "
            "sau despre modelul cel mai bun."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_model_metrics",
        "description": (
            "Returnează metricile de performanță pentru SARIMA, Prophet și XGBoost. "
            "Folosește când utilizatorul compară modele sau întreabă despre acuratețe, "
            "RMSE, MAPE sau modelul câștigător."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_training_runs",
        "description": (
            "Returnează istoricul rulărilor de antrenare. "
            "Folosește când utilizatorul întreabă despre ultima rulare sau istoricul antrenărilor."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_optuna_links",
        "description": (
            "Returnează linkurile, porturile și bazele de date pentru dashboard-urile Optuna. "
            "Folosește când utilizatorul întreabă despre Optuna, tuning sau trial-uri."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "trigger_scrape",
        "description": (
            "Trimite cererea de actualizare a datelor istorice BNR. "
            "Folosește când utilizatorul cere actualizarea cursurilor GBP/RON."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "trigger_train",
        "description": (
            "Returnează instrucțiuni pentru reantrenarea completă a modelelor. "
            "Nu pornește direct pipeline-ul lung, ci explică rularea controlată din terminal."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ═════════════════════════════════════════════════════════════════════════════
# SECȚIUNEA 3: Executorul de tool calls
# ═════════════════════════════════════════════════════════════════════════════

def execute_tool_call(tool_name: str, tool_args: dict[str, Any]) -> str:
    """
    Execută funcția locală corespunzătoare tool_name cu argumentele primite.

    Args:
        tool_name: Numele tool-ului cerut de model.
        tool_args: Dicționarul de argumente extras din cererea modelului.

    Returns:
        String JSON cu rezultatul. Acesta va fi trimis înapoi modelului.
    """
    func = TOOL_REGISTRY.get(tool_name)

    if func is None:
        result = {"success": False, "error": f"Tool necunoscut: '{tool_name}'"}
    else:
        try:
            result = func(**tool_args)
        except TypeError as exc:
            result = {"success": False, "error": f"Argumente invalide pentru '{tool_name}': {exc}"}
        except Exception as exc:
            result = {"success": False, "error": f"Eroare la execuția '{tool_name}': {exc}"}

    return json.dumps(result, ensure_ascii=False)


# ═════════════════════════════════════════════════════════════════════════════
# SECȚIUNEA 4: Agentic Loop – Gemini cu Function Calling
# ═════════════════════════════════════════════════════════════════════════════

def run_bnr_agent(user_message: str, verbose: bool = True) -> str:
    """
    Rulează un agent Gemini care poate apela tool-uri locale pentru a răspunde.

    Args:
        user_message: Întrebarea sau sarcina utilizatorului în limbaj natural.
        verbose: Dacă True, afișează pașii intermediari.

    Returns:
        Răspunsul final al agentului în limbaj natural.

    Raises:
        ImportError: Dacă pachetul google-generativeai nu este instalat.
        ValueError: Dacă GEMINI_API_KEY nu este setat.
    """
    try:
        import google.generativeai as genai
        from google.generativeai.types import FunctionDeclaration, Tool
    except ImportError as exc:
        raise ImportError("Instalează pachetul: pip install google-generativeai") from exc

    if not GEMINI_API_KEY:
        raise ValueError("Setează variabila de mediu GEMINI_API_KEY înainte de a rula agentul.")

    genai.configure(api_key=GEMINI_API_KEY)

    function_declarations = [
        FunctionDeclaration(
            name=tool["name"],
            description=tool["description"],
            parameters=tool["parameters"],
        )
        for tool in TOOLS_SCHEMA
    ]

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        tools=[Tool(function_declarations=function_declarations)],
        system_instruction=(
            "Ești un asistent specializat în analiza cursului valutar GBP/RON "
            "pe baza datelor din aplicația locală curs_bnr_agentic. "
            "Folosești tool-urile disponibile pentru a obține date reale din API "
            "înainte de a formula răspunsuri. "
            "Răspunde concis, clar și în limba română. "
            "Nu inventa valori. Dacă API-ul nu răspunde, explică utilizatorului "
            "că backend-ul FastAPI trebuie pornit cu: python run_api.py."
        ),
    )

    chat = model.start_chat(enable_automatic_function_calling=False)
    response = chat.send_message(user_message)

    iteration = 0
    max_iterations = 5

    while iteration < max_iterations:
        iteration += 1
        candidate = response.candidates[0]
        content = candidate.content

        function_calls = [
            part.function_call
            for part in content.parts
            if hasattr(part, "function_call") and part.function_call.name
        ]

        if not function_calls:
            final_text = "".join(
                part.text for part in content.parts if hasattr(part, "text")
            )
            if verbose:
                print(f"\n[SUCCESS] Raspuns final dupa {iteration - 1} tool call(uri).")
            return final_text.strip()

        function_responses = []

        for function_call in function_calls:
            tool_name = function_call.name
            tool_args = dict(function_call.args)

            if verbose:
                print(f"\n[TOOL] Modelul apeleaza: '{tool_name}' cu args: {tool_args}")

            result_json = execute_tool_call(tool_name, tool_args)

            if verbose:
                print(f"   -> Rezultat: {result_json[:200]}...")

            function_responses.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=tool_name,
                        response={"result": json.loads(result_json)},
                    )
                )
            )

        response = chat.send_message(function_responses)

    return "[WARNING] Agentul a depasit numarul maxim de iteratii fara un raspuns final."


# ═════════════════════════════════════════════════════════════════════════════
# SECȚIUNEA 5: Demo CLI
# python -m curs_bnr.model_utils
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  BNR Agent GBP/RON - Demo Tool Calling")
    print("=" * 60)

    demo_questions = [
        "Care este ultimul curs GBP/RON disponibil?",
        "Ce model face cea mai buna prognoza si care este RMSE-ul lui?",
        "Compara performanta modelelor SARIMA, Prophet si XGBoost.",
        "Cum pot vedea dashboard-urile Optuna?",
    ]

    for question in demo_questions:
        print(f"\n{'-' * 60}")
        print(f"Utilizator: {question}")
        print(f"{'-' * 60}")

        try:
            answer = run_bnr_agent(question, verbose=True)
            print(f"\nAgent: {answer}")
        except (ImportError, ValueError) as exc:
            print(f"[CONFIG] Configurare necesara: {exc}")
            break