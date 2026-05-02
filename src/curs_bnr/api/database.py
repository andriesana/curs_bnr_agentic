import os
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Importam config pentru a gasi calea catre outputs/app_data
from curs_bnr.config import OUTPUTS_DIR

DB_DIR = OUTPUTS_DIR / "app_data"
DB_PATH = DB_DIR / "curs_bnr_app.db"

# Asiguram existenta folderului
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR, exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, unique=True, index=True)
    gbp_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class TrainingRun(Base):
    __tablename__ = "training_runs"
    id = Column(Integer, primary_key=True, index=True)
    run_date = Column(DateTime, default=datetime.utcnow)
    winner_model = Column(String)
    best_rmse = Column(Float)
    report_path = Column(String)
    results = relationship("ModelResult", back_populates="run")

class ModelResult(Base):
    __tablename__ = "model_results"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("training_runs.id"))
    model_name = Column(String)
    rmse = Column(Float)
    mae = Column(Float)
    mape = Column(Float)
    run = relationship("TrainingRun", back_populates="results")

class Forecast(Base):
    __tablename__ = "forecasts"
    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(String)
    predicted_value = Column(Float)
    model_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
