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
    """Uploads multiple files, processes them, and records them in the DB."""
    conn, cursor = get_db_connection()
    uploaded_file_ids = []

    try:
        # Create a new file_set
        file_set_id = uuid4()
        cursor.execute(
            "INSERT INTO file_sets (id) VALUES (%s) RETURNING id;",
            (str(file_set_id),)
        )
        conn.commit()

        for file in files:
            try:
                file_path = save_uploaded_file(file)
                cursor.execute(
                    """
                    INSERT INTO files (id, file_set_id, file_path, original_filename, status)
                    VALUES (%s, %s, %s, %s, 'pending')
                    RETURNING id;
                    """,
                    (str(uuid4()), str(file_set_id), file_path, file.filename),
                )
                file_id = cursor.fetchone()["id"]
                conn.commit()

                # Processing remains similar but updates different status
                output_filename = f"processed_{file.filename}"
                output_path = get_processed_file_path(output_filename)
                if process_file(file_path, output_path):
                    cursor.execute(
                        """
                        UPDATE files
                        SET status = 'processed'
                        WHERE id = %s;
                        """,
                        (str(file_id),),
                    )
                    conn.commit()
                else:
                    cursor.execute(
                        """
                        UPDATE files
                        SET status = 'failed'
                        WHERE id = %s;
                        """,
                        (str(file_id),),
                    )
                    conn.commit()

                uploaded_file_ids.append({"file_id": file_id, "filename": file.filename})

            except Exception as e:
                conn.rollback()
                raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

        return {"file_set_id": file_set_id, "uploaded_files": uploaded_file_ids}

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
