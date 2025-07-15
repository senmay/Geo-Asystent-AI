from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat

app = FastAPI(
    title="Geo-Asystent AI",
    description="Backend for the GIS AI Assistant",
    version="1.0.0"
)

# --- CORRECT CORS Configuration ---
# We explicitly list the origins that are allowed to connect.
# Using a wildcard "*" is not recommended for production and can cause issues.
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(chat.router)

@app.get("/")
def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to Geo-Asystent AI Backend - CORS Fixed Edition"}