from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
import os
import shutil
import uuid
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import threading

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Ensure it is defined in Railway.")

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
except psycopg2.OperationalError as e:
    print("Error connecting to the database:", e)
    raise

# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI is running on Railway!"}

# Ensure necessary tables exist in the database
cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id TEXT NOT NULL,
        project_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
        file_name TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        processed_at TIMESTAMP,
        results JSONB,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')
conn.commit()

# Directory to temporarily store uploaded files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload/")
async def upload_files(
    user_id: str = Form(...), 
    project_name: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Handles file/folder uploads, creates a project record, and logs each file."""
    try:
        # Create a new project entry in the database
        cursor.execute("INSERT INTO projects (user_id, project_name) VALUES (%s, %s) RETURNING id;", (user_id, project_name))
        project_id = cursor.fetchone()["id"]
        conn.commit()

        file_records = []
        for file in files:
            file_id = str(uuid.uuid4())
            file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Insert file record into database
            cursor.execute("INSERT INTO files (id, project_id, file_name, status) VALUES (%s, %s, %s, 'pending');",
                           (file_id, project_id, file.filename))
            conn.commit()
            file_records.append({"file_id": file_id, "file_name": file.filename})
        
        return {"message": "Files uploaded successfully", "project_id": project_id, "files": file_records}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Mock file processing function
def process_file(file_id: str):
    """Mock function that simulates transcript processing and updates DB."""
    time.sleep(5)  # Simulate processing delay
    summary = f"Mock summary of file {file_id}"
    
    cursor.execute("UPDATE files SET status = 'processed', processed_at = NOW(), results = %s WHERE id = %s;",
                   (json.dumps({"summary": summary}), file_id))
    conn.commit()

@app.post("/process/{project_id}")
async def process_project(project_id: str):
    """Triggers processing for all pending files in a given project."""
    cursor.execute("SELECT id FROM files WHERE project_id = %s AND status = 'pending';", (project_id,))
    files = cursor.fetchall()
    
    if not files:
        return {"message": "No pending files to process."}
    
    # Start processing each file in a separate thread
    for file in files:
        threading.Thread(target=process_file, args=(file["id"],)).start()
    
    return {"message": "Processing started for all pending files."}

@app.get("/results/{project_id}")
async def get_results(project_id: str):
    """Fetches processing results for all files in a given project."""
    cursor.execute("SELECT file_name, status, results FROM files WHERE project_id = %s;", (project_id,))
    records = cursor.fetchall()
    return {"project_id": project_id, "results": records}
