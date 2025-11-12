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
    # Only start polling in one process to avoid conflicts
    # With uvicorn workers, each worker runs startup, so we use a file lock
    import os
    import logging
    import atexit
    logger = logging.getLogger(__name__)
    
    # Use a file lock to ensure only one process starts polling
    # Keep the lock file open while polling is active
    try:
        import fcntl
        lock_file_path = "/tmp/max-signal-bot-polling.lock"
        lock_file = open(lock_file_path, 'w')
        try:
            # Try to acquire exclusive non-blocking lock
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            # We got the lock, so we're the one who should start polling
            logger.info("Acquired bot polling lock, starting polling...")
            
            # Store lock file in a global so it stays open
            import app.main as main_module
            main_module._polling_lock_file = lock_file
            
            # Register cleanup on exit
            def release_lock():
                try:
                    if hasattr(main_module, '_polling_lock_file'):
                        fcntl.flock(main_module._polling_lock_file.fileno(), fcntl.LOCK_UN)
                        main_module._polling_lock_file.close()
                except:
                    pass
            atexit.register(release_lock)
            
            db = SessionLocal()
            try:
                await start_bot_polling(db)
                logger.info("Telegram bot polling started successfully")
            except Exception as e:
                logger.warning(f"Could not start Telegram bot polling: {e}")
                # Release lock if polling failed
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                    main_module._polling_lock_file = None
                except:
                    pass
            finally:
                db.close()
        except BlockingIOError:
            # Another process already has the lock, skip polling
            logger.info("Bot polling already started by another process, skipping")
            lock_file.close()
    except ImportError:
        # fcntl not available (Windows), fall back to trying anyway
        # This will cause conflicts with multiple workers, but better than nothing
        logger.warning("fcntl not available, bot polling may conflict with multiple workers")
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
    
    # Release lock file if we have it
    try:
        import app.main as main_module
        if hasattr(main_module, '_polling_lock_file') and main_module._polling_lock_file:
            import fcntl
            try:
                fcntl.flock(main_module._polling_lock_file.fileno(), fcntl.LOCK_UN)
                main_module._polling_lock_file.close()
                main_module._polling_lock_file = None
            except:
                pass
    except:
        pass

