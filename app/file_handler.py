import uuid
import os
import shutil
from typing import List
from fastapi import File, UploadFile, Form
from app.database import cursor, conn
from app.job_handler import create_job, update_job_progress

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_files(user_id: str, project_name: str, files: List[UploadFile]):
    """Handles file uploads and associates them with a job."""
    job_id = create_job(user_id)  # Create a new job

    cursor.execute("INSERT INTO projects (job_id, user_id, project_name) VALUES (%s, %s, %s) RETURNING id;",
                   (job_id, user_id, project_name))
    project_id = cursor.fetchone()["id"]
    conn.commit()

    file_records = []
    for file in files:
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Save file record in DB
        cursor.execute("INSERT INTO files (id, job_id, project_id, file_name, status) VALUES (%s, %s, %s, %s, 'pending');",
                       (file_id, job_id, project_id, file.filename))
        conn.commit()
        file_records.append({"file_id": file_id, "file_name": file.filename})

    return job_id, project_id, file_records
