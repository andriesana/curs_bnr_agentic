from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os

from curs_bnr.api import database, services
from curs_bnr.config import REPORTS_DIR

app = FastAPI(title="BNR Exchange Rate API - GBP/RON")

# Initializare DB si Bootstrap
@app.on_event("startup")
def startup_event():
    database.init_db()
    db = database.SessionLocal()
    try:
        services.bootstrap_data(db)
    finally:
        db.close()

@app.get("/api/rates")
def read_rates(limit: int = 100, db: Session = Depends(database.get_db)):
    rates = services.get_latest_rates(db, limit=limit)
    return rates

@app.get("/api/forecast/latest")
def get_latest_forecast(db: Session = Depends(database.get_db)):
    # Returneaza fallback daca nu exista prognoze reale
    latest_rate = db.query(database.ExchangeRate).order_by(database.ExchangeRate.date.desc()).first()
    latest_run = db.query(database.TrainingRun).order_by(database.TrainingRun.run_date.desc()).first()
    
    if not latest_rate:
        return {"status": "error", "message": "Nu exista date disponibile."}

    # Daca avem un run, inseamna ca am facut bootstrap sau antrenare
    status_text = "Statut: Raport existent" if latest_run else "Statut: Doar date istorice"
    
    response = {
        "last_date": latest_rate.date,
        "last_value": latest_rate.gbp_rate,
        "winner_model": latest_run.winner_model if latest_run else "N/A",
        "best_rmse": latest_run.best_rmse if latest_run else None,
        "forecast_status": status_text
    }
    return response

@app.get("/api/runs")
def read_runs(db: Session = Depends(database.get_db)):
    runs = services.get_all_runs(db)
    return runs

@app.get("/api/metrics")
def get_metrics():
    comp_path = REPORTS_DIR / "optimization_comparison.csv"
    if os.path.exists(comp_path):
        import pandas as pd
        df = pd.read_csv(comp_path)
        return df.to_dict(orient="records")
    return []

@app.get("/api/optuna-links")
def get_optuna_links():
    return services.get_optuna_info()

@app.post("/api/scrape")
def trigger_scrape():
    return {
        "status": "info",
        "message": "Scraping-ul se poate rula manual prin src/curs_bnr/data/scraper.py."
    }

@app.post("/api/train")
def trigger_train():
    return {
        "status": "info",
        "message": "Pentru reantrenare completa (Tuning + Evaluare), rulati in terminal: python main_pipeline.py"
    }
