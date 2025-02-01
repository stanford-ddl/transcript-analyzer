import uuid
from app.database import cursor, conn

def create_job(user_id: str) -> str:
    """Create a new job entry and return the job ID."""
    job_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO jobs (id, user_id, status, progress) VALUES (%s, %s, 'pending', 0.0);",
                   (job_id, user_id))
    conn.commit()
    return job_id

def update_job_progress(job_id: str):
    """Updates the job progress based on the number of processed files."""
    cursor.execute("SELECT COUNT(*) FROM files WHERE job_id = %s;", (job_id,))
    total_files = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM files WHERE job_id = %s AND status = 'processed';", (job_id,))
    processed_files = cursor.fetchone()[0]

    if total_files == 0:
        return  # Avoid division by zero

    progress = (processed_files / total_files) * 100
    status = "completed" if processed_files == total_files else "processing"

    cursor.execute("UPDATE jobs SET progress = %s, status = %s WHERE id = %s;", (progress, status, job_id))
    conn.commit()
