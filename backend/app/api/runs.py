"""
Analysis runs endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from app.core.database import get_db
from app.models.analysis_run import AnalysisRun, RunStatus, TriggerType
from app.models.instrument import Instrument
from app.services.data.adapters import DataService

router = APIRouter()


class CreateRunRequest(BaseModel):
    """Request model for creating a run."""
    instrument: str
    timeframe: str  # M1, M5, M15, H1, D1, etc.


class RunStepResponse(BaseModel):
    """Response model for a run step."""
    step_name: str
    input_blob: Optional[dict] = None
    output_blob: Optional[str] = None
    llm_model: Optional[str] = None
    tokens_used: int = 0
    cost_est: float = 0.0
    created_at: datetime


class RunResponse(BaseModel):
    """Response model for a run."""
    id: int
    trigger_type: str
    instrument: str
    timeframe: str
    status: str
    created_at: datetime
    finished_at: Optional[datetime] = None
    cost_est_total: float = 0.0
    steps: list[RunStepResponse] = []


@router.post("", response_model=RunResponse)
async def create_run(request: CreateRunRequest, db: Session = Depends(get_db)):
    """Create a new analysis run.
    
    For now, this just fetches market data and creates a run record.
    The actual analysis pipeline will be implemented later.
    """
    # Validate instrument exists (for now, just check format)
    # TODO: Check against instruments table
    
    # Fetch market data to validate instrument/timeframe
    data_service = DataService()
    try:
        market_data = data_service.fetch_market_data(
            instrument=request.instrument,
            timeframe=request.timeframe,
            use_cache=True
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch market data: {str(e)}")
    
    # Create or get instrument record
    instrument = db.query(Instrument).filter(Instrument.symbol == request.instrument).first()
    if not instrument:
        # Determine type
        inst_type = "crypto" if "/" in request.instrument.upper() else "equity"
        instrument = Instrument(
            symbol=request.instrument,
            type=inst_type,
            exchange=market_data.exchange or "unknown"
        )
        db.add(instrument)
        db.commit()
        db.refresh(instrument)
    
    # Create run record
    run = AnalysisRun(
        trigger_type=TriggerType.MANUAL,
        instrument_id=instrument.id,
        timeframe=request.timeframe,
        status=RunStatus.QUEUED
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    # For now, immediately mark as succeeded with basic info
    # TODO: This will be replaced with actual pipeline execution
    run.status = RunStatus.SUCCEEDED
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    
    return RunResponse(
        id=run.id,
        trigger_type=run.trigger_type.value,
        instrument=request.instrument,
        timeframe=request.timeframe,
        status=run.status.value,
        created_at=run.created_at,
        finished_at=run.finished_at,
        cost_est_total=run.cost_est_total,
        steps=[]
    )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: int, db: Session = Depends(get_db)):
    """Get analysis run details."""
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get steps
    steps = []
    for step in run.steps:
        steps.append(RunStepResponse(
            step_name=step.step_name,
            input_blob=step.input_blob,
            output_blob=step.output_blob,
            llm_model=step.llm_model,
            tokens_used=step.tokens_used,
            cost_est=step.cost_est,
            created_at=step.created_at
        ))
    
    return RunResponse(
        id=run.id,
        trigger_type=run.trigger_type.value,
        instrument=run.instrument.symbol,
        timeframe=run.timeframe,
        status=run.status.value,
        created_at=run.created_at,
        finished_at=run.finished_at,
        cost_est_total=run.cost_est_total,
        steps=steps
    )


@router.get("", response_model=List[RunResponse])
async def list_runs(limit: int = 20, db: Session = Depends(get_db)):
    """List recent analysis runs."""
    runs = db.query(AnalysisRun).order_by(AnalysisRun.created_at.desc()).limit(limit).all()
    
    result = []
    for run in runs:
        result.append(RunResponse(
            id=run.id,
            trigger_type=run.trigger_type.value,
            instrument=run.instrument.symbol,
            timeframe=run.timeframe,
            status=run.status.value,
            created_at=run.created_at,
            finished_at=run.finished_at,
            cost_est_total=run.cost_est_total,
            steps=[]  # Don't include steps in list view
        ))
    
    return result


@router.post("/{run_id}/publish")
async def publish_run(run_id: int):
    """Publish run to Telegram (to be implemented)."""
    # TODO: Implement Telegram publishing
    return {"message": f"Publish run {run_id} - to be implemented"}


