from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

# For MVP we use SQLite. For Azure Production, replace with CosmosDB/PostgreSQL connection string.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./quantum_telemetry.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class JobTelemetry(Base):
    __tablename__ = "telemetry_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    target_url = Column(String)
    status = Column(String)
    total_tokens = Column(Integer, default=0)
    total_compute_ms = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

def log_telemetry(job_id: str, tokens: int, compute_ms: int):
    """
    Logs ongoing token and compute costs to the billing database.
    """
    db = SessionLocal()
    try:
        job = db.query(JobTelemetry).filter(JobTelemetry.job_id == job_id).first()
        if not job:
            job = JobTelemetry(job_id=job_id, status="running")
            db.add(job)
            
        job.total_tokens = (job.total_tokens or 0) + tokens
        job.total_compute_ms = (job.total_compute_ms or 0) + compute_ms
        # Simplified billing equation for MVP
        job.estimated_cost_usd = (job.total_tokens / 1000) * 0.01 + (job.total_compute_ms / 60000) * 0.05
        
        db.commit()
        return job.estimated_cost_usd
    finally:
        db.close()
