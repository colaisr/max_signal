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
    allow_origins=[
        "http://localhost:3000",      # Frontend dev server (localhost)
        "http://127.0.0.1:3000",      # Frontend dev server (127.0.0.1)
        "http://45.144.177.203:3000",  # Production frontend
    ],
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
    # Only start polling in the main process (not in worker processes)
    # Workers are spawned processes, so check if we're the main process
    import os
    import logging
    logger = logging.getLogger(__name__)
    
    # Check if we're in a worker process (workers have different process names)
    # Main process: "uvicorn app.main:app"
    # Workers: "uvicorn app.main:app" but spawned via multiprocessing
    # Use environment variable or process name to detect main process
    # For uvicorn with workers, only the main process should start polling
    # We'll use a file lock to ensure only one instance polls
    
    try:
        import fcntl
        lock_file_path = "/tmp/max-signal-bot-polling.lock"
        lock_file = open(lock_file_path, 'w')
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            # We got the lock, so we're the one who should start polling
            db = SessionLocal()
            try:
                await start_bot_polling(db)
            except Exception as e:
                logger.warning(f"Could not start Telegram bot polling: {e}")
            finally:
                db.close()
        except BlockingIOError:
            # Another process already has the lock, skip polling
            logger.info("Bot polling already started by another process, skipping")
        finally:
            lock_file.close()
    except ImportError:
        # fcntl not available (Windows), fall back to trying anyway
        # This will cause conflicts with multiple workers, but better than nothing
        db = SessionLocal()
        try:
            await start_bot_polling(db)
        except Exception as e:
            logger.warning(f"Could not start Telegram bot polling: {e}")
        finally:
            db.close()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await stop_bot_polling()

