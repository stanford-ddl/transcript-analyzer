from backend.celery_config import celery_app
from backend.file_handler import save_uploaded_file, get_processed_file_path
from backend.processing import process_file
from backend.database import get_db_connection, release_db_connection
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
        release_db_connection(conn, cursor)

@celery_app.task(bind=True)
def process_file_set(self, file_set_id: str):
    """Process all files in a file set"""
    conn, cursor = get_db_connection()
    try:
        cursor.execute(
            """
            SELECT id, original_filename, file_path
            FROM files
            WHERE file_set_id = %s AND status = 'pending'
            """,
            (file_set_id,)
        )
        files = cursor.fetchall()
        
        results = []
        for file in files:
            output_filename = f"processed_{file['original_filename']}"
            output_path = get_processed_file_path(output_filename)
            
            if process_file(file['file_path'], output_path):
                cursor.execute(
                    """
                    UPDATE files
                    SET status = 'processed'
                    WHERE id = %s;
                    """,
                    (file['id'],)
                )
                results.append({"file_id": file['id'], "status": "success"})
            else:
                cursor.execute(
                    """
                    UPDATE files
                    SET status = 'failed'
                    WHERE id = %s;
                    """,
                    (file['id'],)
                )
                results.append({"file_id": file['id'], "status": "failed"})
            conn.commit()
            
        return {"status": "success", "results": results}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        release_db_connection(conn, cursor)