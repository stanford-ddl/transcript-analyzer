# app/config.py (using Codespaces secrets directly - the RIGHT way)
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
  # Or construct it from individual parts, IF you have a good reason:
  POSTGRES_USER = os.environ.get("POSTGRES_USER")
  POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
  POSTGRES_DB = os.environ.get("POSTGRES_DB")
  POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "db") # 'db' for Docker Compose

  if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST]):
      raise RuntimeError("Missing required database environment variables.")

  DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"