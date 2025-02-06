import os
import shutil
from uuid import uuid4
from fastapi import UploadFile, HTTPException

# 1. Define Storage Directories:
UPLOAD_DIR = "/storage/inputs"  # Primary upload directory (Railway volume).
PROCESSED_DIR = "/storage/outputs"  # Directory for processed files.

# 2. Directory Creation Function:
def create_upload_directory():
    """Ensures the upload and processed directories exist."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

# 3. Save Uploaded File Function (with Filename Collision Check):
def save_uploaded_file(file: UploadFile) -> str:
    """Saves an uploaded file, checking for filename collisions and retrying.

    Args:
        file: The UploadFile object.

    Returns:
        The full path to the saved file.

    Raises:
        HTTPException: If the file extension is invalid.
    """
    create_upload_directory()

    # File Extension Check
    allowed_extensions = {".xlsx", ".csv"}
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only {', '.join(allowed_extensions)} are allowed."
        )

    # --- Generate Unique Filename with Collision Check ---
    max_attempts = 10  # Limit the number of attempts to avoid infinite loops.
    for attempt in range(max_attempts):
        unique_filename = f"{uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Check if a file with this name already exists in the UPLOAD_DIR.
        if not os.path.exists(file_path):
            break  # Filename is unique, exit the loop.
        else:
             print(f"Filename collision detected: {unique_filename}, retrying...")
    else:  # This 'else' belongs to the 'for' loop. It executes if the loop completes without 'break'.
        raise HTTPException(
            status_code=500, detail="Failed to generate a unique filename."
        )

    # Save the file:
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path

# 4. Get File Path Functions:
def get_file_path(filename: str) -> str:
    """Constructs the full path for an uploaded file (in UPLOAD_DIR)."""
    return os.path.join(UPLOAD_DIR, filename)

def get_processed_file_path(filename: str) -> str:
    """Constructs the full path for a processed file (in PROCESSED_DIR)."""
    return os.path.join(PROCESSED_DIR, filename)

# 5. Delete File Function:
def delete_file(file_path: str):
    """Deletes a file."""
    try:
        os.remove(file_path)
        return True
    except FileNotFoundError:
        return False
    except OSError as e:
        print(f"Error deleting file: {e}")
        return False

# 6. Placeholder Processing Function:
def process_file(input_path: str, output_path: str):
    """Placeholder for file processing. REPLACE THIS."""
    try:
        # *** REPLACE THIS WITH YOUR ACTUAL PROCESSING LOGIC ***
        shutil.copyfile(input_path, output_path)  # Example: Copy the file.
        return True
    except Exception as e:
        print(f"Error processing file: {e}")
        return False
