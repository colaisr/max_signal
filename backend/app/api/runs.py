"""
Analysis runs endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()


@router.post("")
async def create_run():
    """Create a new analysis run (to be implemented)."""
    # TODO: Implement run creation
    return {"message": "Create run endpoint - to be implemented"}


@router.get("/{run_id}")
async def get_run(run_id: int, db: Session = Depends(get_db)):
    """Get analysis run details (to be implemented)."""
    # TODO: Implement run retrieval
    return {"message": f"Get run {run_id} - to be implemented"}


@router.post("/{run_id}/publish")
async def publish_run(run_id: int):
    """Publish run to Telegram (to be implemented)."""
    # TODO: Implement Telegram publishing
    return {"message": f"Publish run {run_id} - to be implemented"}

