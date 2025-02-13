from fastapi import FastAPI
import uvicorn
from backend.routes import router  # Import all routes

app = FastAPI()

# Include routes from `routes.py`
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
