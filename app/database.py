import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Ensure it is defined in Railway.")

# Connect to PostgreSQL database
try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("Successfully connected to the database!") # Good for debugging
except psycopg2.OperationalError as e:
    print("Error connecting to the database:", e)
    raise

def get_db_connection():
    """
    Returns the database connection and cursor.  This is a helper function
    to make it easier to access the connection from other modules.
    """
    return conn, cursor
