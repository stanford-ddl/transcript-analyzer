from fastapi import APIRouter
from app.database import cursor

router = APIRouter()

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Fetch job progress and status."""
    cursor.execute("SELECT * FROM jobs WHERE id = %s;", (job_id,))
    job = cursor.fetchone()

    if not job:
        return {"message": "Job not found"}

    return {
        "job_id": job["id"],
        "status": job["status"],
        "progress": job["progress"]
    }
