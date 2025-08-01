from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from middleware import setup_exception_handlers, setup_logging_middleware, setup_monitoring_middleware
from api.routers import chat_router, layers_router

# Get application settings
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Set up logging middleware (should be first)
setup_logging_middleware(app)

# Set up monitoring middleware
setup_monitoring_middleware(app)

# Set up error handling
setup_exception_handlers(app)

# CORS Configuration using centralized settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://mapiarz.pl",
        "http://geoai.mapiarz.pl",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(layers_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "docs_url": "/api/docs",
        "api_prefix": "/api/v1"
    }