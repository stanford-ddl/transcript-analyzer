import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Ensure it is defined in your environment.")

# Create a connection pool
# Adjust minconn and maxconn as needed for your expected load
db_pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)

def get_db_connection():
    """
    Gets a connection from the pool and returns it along with a cursor.
    """
    conn = db_pool.getconn()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cursor

def release_db_connection(conn, cursor):
    """
    Releases the connection back to the pool.  MUST be called after using a connection.
    """
    cursor.close()
    db_pool.putconn(conn)
