from fastapi import FastAPI
from app.routes import router  # Import all routes

app = FastAPI()

# Include routes from `routes.py`
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "FastAPI is running on Railway!"}
