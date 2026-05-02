import pandas as pd
import os
from sqlalchemy.orm import Session
from curs_bnr.api.database import ExchangeRate, TrainingRun, ModelResult
from curs_bnr.config import CSV_PATH, REPORTS_DIR, OPTUNA_STUDIES_DIR

def bootstrap_data(db: Session):
    """Populeaza baza de date la prima pornire folosind fisierele CSV existente."""
    # 1. Incarca datele istorice din CSV daca exchange_rates este goala
    if db.query(ExchangeRate).count() == 0:
        if os.path.exists(CSV_PATH):
            try:
                df = pd.read_csv(CSV_PATH)
                rates = []
                for _, row in df.iterrows():
                    rates.append(ExchangeRate(date=row['date'], gbp_rate=row['gbp_rate']))
                db.bulk_save_objects(rates)
                db.commit()
                print(f"[BOOTSTRAP] Incarcat {len(df)} rate din CSV.")
            except Exception as e:
                print(f"[ERROR] Bootstrap rate esuat: {e}")

    # 2. Incarca rezultatele antrenarii din optimization_comparison.csv
    if db.query(TrainingRun).count() == 0:
        comp_path = REPORTS_DIR / "optimization_comparison.csv"
        if os.path.exists(comp_path):
            try:
                df_comp = pd.read_csv(comp_path)
                if not df_comp.empty:
                    # Determinam numele coloanelor corecte (case sensitive)
                    c_model = 'Model' if 'Model' in df_comp.columns else 'model'
                    c_variant = 'Variant' if 'Variant' in df_comp.columns else 'variant'
                    c_rmse = 'RMSE' if 'RMSE' in df_comp.columns else 'rmse'
                    c_mape = 'MAPE' if 'MAPE' in df_comp.columns else 'mape'
                    c_mae = 'MAE' if 'MAE' in df_comp.columns else 'mae'

                    # Gasim modelul cu cel mai mic RMSE
                    winner_idx = df_comp[c_rmse].idxmin()
                    winner_row = df_comp.loc[winner_idx]
                    winner_name = f"{winner_row[c_model]} ({winner_row[c_variant]})"

                    run = TrainingRun(
                        winner_model=winner_name,
                        best_rmse=float(winner_row[c_rmse]),
                        report_path=str(comp_path)
                    )
                    db.add(run)
                    db.flush() 

                    for _, row in df_comp.iterrows():
                        res = ModelResult(
                            run_id=run.id,
                            model_name=f"{row[c_model]} ({row[c_variant]})",
                            rmse=float(row[c_rmse]),
                            mae=float(row.get(c_mae, 0.0)),
                            mape=float(row[c_mape])
                        )
                        db.add(res)
                    db.commit()
                    print(f"[BOOTSTRAP] Incarcat rezultate antrenare. Castigator: {winner_name}")
            except Exception as e:
                print(f"[ERROR] Bootstrap rezultate esuat: {e}")

def get_latest_rates(db: Session, limit: int = 14):
    return db.query(ExchangeRate).order_by(ExchangeRate.date.desc()).limit(limit).all()

def get_all_runs(db: Session):
    return db.query(TrainingRun).order_by(TrainingRun.run_date.desc()).all()

def get_optuna_info():
    studies = ["xgboost", "sarima", "prophet"]
    info = []
    for s in studies:
        db_file = f"{s}_optimization.db"
        db_path = OPTUNA_STUDIES_DIR / db_file
        exists = os.path.exists(db_path)
        port = 7771 if s == "xgboost" else (7772 if s == "sarima" else 7773)
        info.append({
            "model": s.upper(),
            "db_path": str(db_path),
            "exists": exists,
            "port": port,
            "dashboard_url": f"http://localhost:{port}"
        })
    return info
