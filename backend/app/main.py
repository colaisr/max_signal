"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, runs, auth, instruments, analyses, settings
from app.core.config import get_settings

app_settings = get_settings()

app = FastAPI(
    title="Max Signal Bot API",
    description="Market analysis and trading signal generation API",
    version="0.1.0",
)

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(instruments.router, prefix="/api/instruments", tags=["instruments"])
app.include_router(analyses.router, prefix="/api/analyses", tags=["analyses"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # TODO: Initialize scheduler, database connections, etc.
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    # TODO: Close connections, stop scheduler, etc.
    pass

