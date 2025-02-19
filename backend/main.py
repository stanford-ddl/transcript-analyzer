from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from backend.routes import router  # Import all routes

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # Allow requests from Plasmic's domain and other devcontainers
    allow_origins=[
        "http://localhost:3000", 
        "https://studio.plasmic.app",
        "http://localhost:*",  # Allow all localhost ports
        "http://host.docker.internal:*"  # Special Docker DNS name to access host
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes from `routes.py`
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
