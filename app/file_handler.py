import os
import shutil
from uuid import uuid4
from fastapi import UploadFile, HTTPException

# 1. Define Storage Directories:
# Dynamically determine the Codespace name
CODESPACE_NAME = os.environ.get("CODESPACE_NAME", "your-default-codespace-name")  # Provide a default

# Construct the paths relative to the Codespace root
UPLOAD_DIR = f"/workspaces/{CODESPACE_NAME}/.devcontainer/storage/inputs"
PROCESSED_DIR = f"/workspaces/{CODESPACE_NAME}/.devcontainer/storage/outputs"

# 2. Directory Creation Function:
def create_upload_directory():
    """Ensures the upload and processed directories exist."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

# 3. Save Uploaded File Function (with Filename Collision Check):
def save_uploaded_file(file: UploadFile) -> str:
    """Saves an uploaded file, checking for filename collisions and retrying."""
    create_upload_directory()

    # File Extension Check
    allowed_extensions = {".xlsx", ".csv"}
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only {', '.join(allowed_extensions)} are allowed."
        )

    # Generate Unique Filename with Collision Check
    max_attempts = 10
    for attempt in range(max_attempts):
        unique_filename = f"{uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        if not os.path.exists(file_path):
            break
        else:
             print(f"Filename collision detected: {unique_filename}, retrying...")
    else:
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
