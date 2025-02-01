import asyncio
import aiohttp
import json
from app.database import cursor, conn
from app.job_handler import update_job_progress

API_URL = "https://api.anthropic.com/v1/messages"
API_KEY = "YOUR_ACTUAL_API_KEY"

async def analyze_utterance(text: str):
    """Sends an utterance to Anthropic API for analysis."""
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": text}]
    }

    headers = {
        "x-api-key": API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=payload) as response:
            return await response.json()

async def process_file(file_id: str, file_path: str, job_id: str):
    """Reads a transcript file and processes each utterance."""
    with open(file_path, 'r') as f:
        data = json.load(f)

    utterances = data.get("utterances", [])
    processed_utterances = await asyncio.gather(*[analyze_utterance(u["text"]) for u in utterances])

    # Update DB
    cursor.execute("UPDATE files SET status = 'processed', results = %s WHERE id = %s;",
                   (json.dumps(processed_utterances), file_id))
    conn.commit()

    # Update job progress
    update_job_progress(job_id)

def process_job(job_id: str):
    """Processes all pending files for a job and updates progress."""
    cursor.execute("SELECT id, file_name FROM files WHERE job_id = %s AND status = 'pending';", (job_id,))
    files = cursor.fetchall()

    if not files:
        return {"message": "No pending files to process."}

    for file in files:
        file_id = file["id"]
        file_path = f"uploads/{file_id}_{file['file_name']}"
        asyncio.run(process_file(file_id, file_path, job_id))

    return {"message": "Processing started for all pending files."}
