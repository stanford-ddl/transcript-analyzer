from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from app.database import get_db_connection  # Import the connection function
from app.file_handler import (
    save_uploaded_file,
    get_processed_file_path,
    process_file,
)
from uuid import UUID
import os
from fastapi.responses import FileResponse

router = APIRouter()

# --- Upload Multiple Files ---
@router.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile] = File(...)):
    """Uploads multiple files, processes them, and records them in the DB."""
    conn, cursor = get_db_connection()  # Get database connection and cursor.
    uploaded_file_ids = []

    for file in files:
        try:
            # 1. Save the file (file_handler.py handles unique names and validation).
            file_path = save_uploaded_file(file)

            # 2. Insert file metadata into the database.
            cursor.execute(
                """
                INSERT INTO files (file_name, status)
                VALUES (%s, 'pending')
                RETURNING id;
                """,
                (file.filename,),  # Store the *original* filename.
            )
            file_id = cursor.fetchone()["id"]
            conn.commit()  # Commit after each successful file upload and insert.

            # 3. Process the file (using the placeholder function).
            output_filename = f"processed_{file.filename}"
            output_path = get_processed_file_path(output_filename)
            if process_file(file_path, output_path):
                # 4. Update database with processed status.
                cursor.execute(
                    """
                    UPDATE files
                    SET status = 'processed', processed_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                    """,
                    (file_id,),
                )
                conn.commit() # Commit after each successful file process and update
            else:
                #If processing fails, update to a failed status
                cursor.execute(
                    """
                    UPDATE files
                    SET status = 'failed'
                    WHERE id = %s;
                    """,
                    (file_id,),
                )
                conn.commit()

            uploaded_file_ids.append({"file_id": file_id, "filename": file.filename})

        except HTTPException as e:  # Catch HTTP exceptions (e.g., from file_handler).
            conn.rollback()  # Rollback if any error occurred during file save/insert.
            raise e  # Re-raise the exception to return the error to the client.
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    return {"uploaded_files": uploaded_file_ids}


# --- Download a File ---
@router.get("/download/{file_id}")
async def download_file(file_id: UUID):
    """Downloads a processed file by its ID."""
    conn, cursor = get_db_connection()
    cursor.execute(
        "SELECT file_name, status FROM files WHERE id = %s;", (file_id,)
    )
    file_info = cursor.fetchone()

    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    if file_info["status"] != "processed":
        raise HTTPException(status_code=400, detail="File not processed yet")

    # Construct the path to the *processed* file.
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
