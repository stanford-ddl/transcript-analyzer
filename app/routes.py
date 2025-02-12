from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from app.database import get_db_connection
from app.file_handler import (
    save_uploaded_file,
    get_processed_file_path,
)
from app.processing import process_file
from uuid import UUID, uuid4
import os
from fastapi.responses import FileResponse

router = APIRouter()

# --- Upload Multiple Files ---
@router.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile] = File(...)):
    """Uploads multiple files and queues them for processing."""
    conn, cursor = get_db_connection()
    uploaded_file_ids = []

    try:
        # Create a new file_set
        file_set_id = str(uuid4())
        cursor.execute(
            "INSERT INTO file_sets (id) VALUES (%s) RETURNING id;",
            (file_set_id,)
        )
        conn.commit()

        for file in files:
            file_id = str(uuid4())
            
            # Read file content
            file_content = await file.read()
            
            # Create file record with pending status
            cursor.execute(
                """
                INSERT INTO files (id, file_set_id, original_filename, status)
                VALUES (%s, %s, %s, 'pending')
                RETURNING id;
                """,
                (file_id, file_set_id, file.filename)
            )
            conn.commit()

            # Queue the file processing task
            process_uploaded_file.delay(
                file_id,
                file_set_id,
                file_content,
                file.filename
            )

            uploaded_file_ids.append({"file_id": file_id, "filename": file.filename})

        return {
            "message": "Files uploaded and queued for processing",
            "file_set_id": file_set_id,
            "uploaded_files": uploaded_file_ids
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        cursor.close()


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