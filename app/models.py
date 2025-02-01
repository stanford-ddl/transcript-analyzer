from app.database import cursor, conn

# Ensure necessary tables exist in the database
cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id TEXT NOT NULL,
        project_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
        file_name TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        processed_at TIMESTAMP,
        results JSONB,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')
conn.commit()
