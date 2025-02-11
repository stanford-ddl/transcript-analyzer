import os
import psycopg2
from psycopg2.extras import RealDictCursor

# --- Construct DATABASE_URL from individual environment variables ---
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DB = os.environ.get("POSTGRES_DB")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"
# --- End of DATABASE_URL construction ---

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
