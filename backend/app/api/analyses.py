"""
API endpoints for analysis types.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.core.database import get_db
from app.models.analysis_type import AnalysisType
from app.core.auth import get_current_admin_user_dependency
from app.models.user import User

router = APIRouter()


class AnalysisTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    display_name: str
    description: str | None
    version: str
    config: dict
    is_active: int
    created_at: datetime
    updated_at: datetime


@router.get("", response_model=List[AnalysisTypeResponse])
async def list_analysis_types(db: Session = Depends(get_db)):
    """List all active analysis types."""
    analysis_types = db.query(AnalysisType).filter(AnalysisType.is_active == 1).all()
    return analysis_types


@router.get("/{analysis_type_id}", response_model=AnalysisTypeResponse)
async def get_analysis_type(analysis_type_id: int, db: Session = Depends(get_db)):
    """Get analysis type details by ID."""
    analysis_type = db.query(AnalysisType).filter(AnalysisType.id == analysis_type_id).first()
    if not analysis_type:
        raise HTTPException(status_code=404, detail="Analysis type not found")
    return analysis_type


@router.get("/name/{name}", response_model=AnalysisTypeResponse)
async def get_analysis_type_by_name(name: str, db: Session = Depends(get_db)):
    """Get analysis type by name (e.g., 'daystart')."""
    analysis_type = db.query(AnalysisType).filter(AnalysisType.name == name).first()
    if not analysis_type:
        raise HTTPException(status_code=404, detail="Analysis type not found")
    return analysis_type


class UpdateAnalysisTypeConfigRequest(BaseModel):
    """Request model for updating analysis type configuration."""
    config: Dict[str, Any]


@router.put("/{analysis_type_id}/config", response_model=AnalysisTypeResponse)
async def update_analysis_type_config(
    analysis_type_id: int,
    request: UpdateAnalysisTypeConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user_dependency)
):
    """Update analysis type configuration (admin only)."""
    analysis_type = db.query(AnalysisType).filter(AnalysisType.id == analysis_type_id).first()
    if not analysis_type:
        raise HTTPException(status_code=404, detail="Analysis type not found")
    
    # Validate config structure
    if "steps" not in request.config:
        raise HTTPException(status_code=400, detail="Config must contain 'steps' array")
    
    # Update config
    analysis_type.config = request.config
    db.commit()
    db.refresh(analysis_type)
    
    return analysis_type
