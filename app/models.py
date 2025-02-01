from app.database import cursor, conn

# Create a new table for jobs
cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id TEXT NOT NULL,
        status TEXT DEFAULT 'pending',  -- Status: pending, processing, completed
        progress FLOAT DEFAULT 0.0,  -- Progress percentage (0-100)
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')

# Ensure necessary tables exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
        user_id TEXT NOT NULL,
        project_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
        job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
        file_name TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        processed_at TIMESTAMP,
        results JSONB,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')
conn.commit()
