"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, runs, auth, instruments, analyses, settings
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.telegram.bot_handler import start_bot_polling, stop_bot_polling

app_settings = get_settings()

app = FastAPI(
    title="Max Signal Bot API",
    description="Market analysis and trading signal generation API",
    version="0.1.2",  # Deployment test v2
)

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://45.144.177.203:3000"],  # Frontend dev server + production
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
    # Start Telegram bot polling to handle /start commands
    # We create a temporary session just to get the bot token
    db = SessionLocal()
    try:
        await start_bot_polling(db)
    except Exception as e:
        # Log error but don't fail startup if bot token is not configured
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not start Telegram bot polling: {e}")
    finally:
        db.close()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await stop_bot_polling()

