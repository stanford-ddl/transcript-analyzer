from app.celery_config import celery_app
from app.file_handler import save_uploaded_file, get_processed_file_path
from app.processing import process_file
from app.database import get_db_connection
from uuid import uuid4

@celery_app.task(bind=True)
def process_uploaded_file(self, file_id: str, file_set_id: str, file_data: bytes, filename: str):
    """Process a single uploaded file"""
    conn, cursor = get_db_connection()
    try:
        # Save file to disk
        file_path = save_uploaded_file(file_data, filename)
        
        # Update database with file path
        cursor.execute(
            """
            UPDATE files 
            SET file_path = %s, status = 'saving'
            WHERE id = %s
            """,
            (file_path, file_id)
        )
        conn.commit()

        # Process the file
        output_filename = f"processed_{filename}"
        output_path = get_processed_file_path(output_filename)
        
        if process_file(file_path, output_path):
            cursor.execute(
                """
                UPDATE files
                SET status = 'processed'
                WHERE id = %s;
                """,
                (file_id,)
            )
        else:
            cursor.execute(
                """
                UPDATE files
                SET status = 'failed'
                WHERE id = %s;
                """,
                (file_id,)
            )
        conn.commit()
        
        return {"status": "success", "file_id": file_id}
        
    except Exception as e:
        cursor.execute(
            """
            UPDATE files
            SET status = 'failed'
            WHERE id = %s;
            """,
            (file_id,)
        )
        conn.commit()
        return {"status": "error", "error": str(e)}
    finally:
        cursor.close()