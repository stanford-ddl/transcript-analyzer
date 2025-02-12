from fastapi import APIRouter, UploadFile, File, HTTPException, Response, BackgroundTasks
from app.database import get_db_connection, release_db_connection
from app.file_handler import (
    save_uploaded_file,
    get_processed_file_path,
    save_uploaded_file_streaming,
    MAX_FILE_SIZE,
)
from app.processing import process_file
from uuid import UUID, uuid4
import os
from fastapi.responses import FileResponse
from app.tasks import process_uploaded_file, process_file_set
from celery.result import AsyncResult

router = APIRouter()

# Constants specific to batch uploads
MAX_FILES = 100
MAX_BATCH_SIZE = 500 * 1024 * 1024  # 500MB total per request

# --- Upload Multiple Files ---
@router.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile] = File(...)):
    """Handle batch file upload"""
    # Validate request-level constraints
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum is {MAX_FILES} files"
        )
    
    # Validate total batch size
    total_size = sum(f.size for f in files if hasattr(f, 'size'))
    if total_size > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Total batch size too large. Maximum is {MAX_BATCH_SIZE/1024/1024}MB"
        )
    
    conn, cursor = get_db_connection()
    uploaded_files = []
    
    try:
        file_set_id = str(uuid4())
        cursor.execute(
            "INSERT INTO file_sets (id) VALUES (%s) RETURNING id;",
            (file_set_id,)
        )
        conn.commit()

        for file in files:
            file_id = str(uuid4())
            
            try:
                # Stream and save file
                file_path = await save_uploaded_file_streaming(file)
                
                # Update database and queue processing
                cursor.execute(
                    """
                    INSERT INTO files (id, file_set_id, original_filename, status)
                    VALUES (%s, %s, %s, 'pending')
                    RETURNING id;
                    """,
                    (file_id, file_set_id, file.filename)
                )
                conn.commit()

                # Queue processing task
                task = process_uploaded_file.delay(
                    file_id,
                    file_set_id,
                    file_path,
                    file.filename
                )

                uploaded_files.append({
                    "file_id": file_id,
                    "filename": file.filename,
                    "task_id": task.id
                })

            except HTTPException as he:
                # Re-raise HTTP exceptions (like validation errors)
                raise he
            except Exception as e:
                # Handle other errors
                cursor.execute(
                    "UPDATE files SET status = 'failed' WHERE id = %s",
                    (file_id,)
                )
                conn.commit()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process {file.filename}: {str(e)}"
                )

        return {
            "message": "Files uploaded successfully",
            "file_set_id": file_set_id,
            "uploaded_files": uploaded_files
        }

    finally:
        release_db_connection(conn, cursor)


# --- Download a File ---
@router.get("/download/{file_id}")
async def download_file(file_id: UUID):
    """Downloads a processed file by its ID."""
    conn, cursor = get_db_connection()
    cursor.execute(
        "SELECT original_filename, status, file_path FROM files WHERE id = %s;",
        (str(file_id),)
    )
    file_info = cursor.fetchone()

    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    if file_info["status"] != "processed":
        raise HTTPException(status_code=400, detail="File not processed yet")

    original_filename = file_info["original_filename"]
    processed_filename = f"processed_{original_filename}"
    file_path = get_processed_file_path(processed_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Processed file not found on server")

    return FileResponse(
        file_path, filename=original_filename, media_type="application/octet-stream"
    )


# --- List Files ---
@router.get("/files")
async def list_files():
    """Lists all files and their statuses."""
    conn, cursor = get_db_connection()
    cursor.execute("""
        SELECT f.id, f.original_filename, f.status, f.created_at, f.file_set_id
        FROM files f
        LEFT JOIN file_sets fs ON f.file_set_id = fs.id
        ORDER BY f.created_at DESC;
    """)
    files = cursor.fetchall()
    return files

@router.get("/status/{file_set_id}")
async def get_processing_status(file_set_id: str):
    """Get the processing status of all files in a file set."""
    conn, cursor = get_db_connection()
    try:
        cursor.execute(
            """
            SELECT id, original_filename, status
            FROM files
            WHERE file_set_id = %s
            """,
            (file_set_id,)
        )
        files = cursor.fetchall()
        
        if not files:
            raise HTTPException(status_code=404, detail="File set not found")
            
        return {
            "file_set_id": file_set_id,
            "files": files
        }
    finally:
        cursor.close()

# Add this new endpoint to check task status
@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a Celery task"""
    task_result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }

@router.get("/upload-progress/{file_set_id}")
async def get_upload_progress(file_set_id: str):
    conn, cursor = get_db_connection()
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_files,
                COUNT(CASE WHEN status = 'processed' THEN 1 END) as processed,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN status = 'uploading' THEN 1 END) as uploading
            FROM files 
            WHERE file_set_id = %s
        """, (file_set_id,))
        
        stats = cursor.fetchone()
        return {
            "file_set_id": file_set_id,
            "total_files": stats['total_files'],
            "processed": stats['processed'],
            "failed": stats['failed'],
            "uploading": stats['uploading'],
            "progress_percentage": (stats['processed'] / stats['total_files'] * 100) if stats['total_files'] > 0 else 0
        }
    finally:
        release_db_connection(conn, cursor)