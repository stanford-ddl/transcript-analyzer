from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from app.database import get_db_connection
from app.file_handler import (
    save_uploaded_file,
    get_processed_file_path,
)
from app.processing import process_file
from uuid import UUID
import os
from fastapi.responses import FileResponse

router = APIRouter()

# --- Upload Multiple Files ---
@router.post("/uploadfiles/")  # No project_id
async def create_upload_files(files: list[UploadFile] = File(...)):
    """Uploads multiple files, processes them, and records them in the DB."""
    conn, cursor = get_db_connection()
    uploaded_file_ids = []

    for file in files:
        try:
            file_path = save_uploaded_file(file)
            cursor.execute(
                """
                INSERT INTO files (file_name, status)  -- No project_id
                VALUES (%s, 'pending')
                RETURNING id;
                """,
                (file.filename,),
            )
            file_id = cursor.fetchone()["id"]
            conn.commit()

            # --- Processing (Simplified for brevity) ---
            output_filename = f"processed_{file.filename}"
            output_path = get_processed_file_path(output_filename)
            if process_file(file_path, output_path):
                cursor.execute(
                    """
                    UPDATE files
                    SET status = 'processed', processed_at = CURRENT_TIMESTAMP
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
            # ---

            uploaded_file_ids.append({"file_id": file_id, "filename": file.filename})

        except HTTPException as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
        finally:
            cursor.close()

    return {"uploaded_files": uploaded_file_ids}


# --- Download a File ---
@router.get("/download/{file_id}")
async def download_file(file_id: UUID):
    """Downloads a processed file by its ID."""
    conn, cursor = get_db_connection()
    cursor.execute(
        "SELECT file_name, status FROM files WHERE id = %s;", (str(file_id),)  # Convert UUID to string
    )
    file_info = cursor.fetchone()

    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    if file_info["status"] != "processed":
        raise HTTPException(status_code=400, detail="File not processed yet")

    original_filename = file_info["file_name"]
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
    cursor.execute("SELECT id, file_name, status, uploaded_at, processed_at FROM files;")
    files = cursor.fetchall()
    return files
