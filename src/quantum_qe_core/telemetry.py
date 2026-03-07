from src.quantum_qe_core.db import SessionLocal, JobTelemetry

def log_telemetry(job_id: str, tokens: int, compute_ms: int, project_id: int = None):
    """
    Logs ongoing token and compute costs to the billing database.
    """
    db = SessionLocal()
    try:
        job = db.query(JobTelemetry).filter(JobTelemetry.job_id == job_id).first()
        if not job:
            job = JobTelemetry(job_id=job_id, project_id=project_id, status="running")
            db.add(job)
            
        job.total_tokens = (job.total_tokens or 0) + tokens
        job.total_compute_ms = (job.total_compute_ms or 0) + compute_ms
        # Simplified billing equation for MVP
        job.estimated_cost_usd = (job.total_tokens / 1000) * 0.01 + (job.total_compute_ms / 60000) * 0.05
        
        db.commit()
        return job.estimated_cost_usd
    finally:
        db.close()
