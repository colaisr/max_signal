"""
Analysis pipeline orchestrator.
Runs the Daystart analysis through all steps: Wyckoff, SMC, VSA, Delta, ICT, Merge.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.analysis_run import AnalysisRun, RunStatus
from app.models.analysis_step import AnalysisStep
from app.services.data.adapters import DataService
from app.services.llm.client import LLMClient
from app.services.analysis.steps import (
    WyckoffAnalyzer,
    SMCAnalyzer,
    VSAAnalyzer,
    DeltaAnalyzer,
    ICTAnalyzer,
    MergeAnalyzer,
)
import logging

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Orchestrates the complete analysis pipeline."""
    
    def __init__(self):
        self.data_service = DataService()
        self.llm_client = LLMClient()
        self.steps = [
            ("wyckoff", WyckoffAnalyzer()),
            ("smc", SMCAnalyzer()),
            ("vsa", VSAAnalyzer()),
            ("delta", DeltaAnalyzer()),
            ("ict", ICTAnalyzer()),
            ("merge", MergeAnalyzer()),
        ]
    
    def run(
        self,
        run: AnalysisRun,
        db: Session,
    ) -> AnalysisRun:
        """Execute the complete analysis pipeline.
        
        Args:
            run: AnalysisRun database record
            db: Database session
            
        Returns:
            Updated AnalysisRun with all steps completed
        """
        try:
            # Update status to running
            run.status = RunStatus.RUNNING
            db.commit()
            
            # Fetch market data
            logger.info("fetching_market_data", run_id=run.id, instrument=run.instrument.symbol)
            market_data = self.data_service.fetch_market_data(
                instrument=run.instrument.symbol,
                timeframe=run.timeframe,
                use_cache=True
            )
            
            # Prepare context for all steps
            context = {
                "instrument": run.instrument.symbol,
                "timeframe": run.timeframe,
                "market_data": market_data,
                "previous_steps": {},
            }
            
            total_cost = 0.0
            
            # Run each analysis step
            for step_name, analyzer in self.steps:
                logger.info("running_step", run_id=run.id, step=step_name)
                
                try:
                    # Run the step (sync call)
                    step_result = analyzer.analyze(
                        context=context,
                        llm_client=self.llm_client,
                    )
                    
                    # Save step to database
                    step_record = AnalysisStep(
                        run_id=run.id,
                        step_name=step_name,
                        input_blob=step_result.get("input"),
                        output_blob=step_result.get("output"),
                        llm_model=step_result.get("model"),
                        tokens_used=step_result.get("tokens_used", 0),
                        cost_est=step_result.get("cost_est", 0.0),
                    )
                    db.add(step_record)
                    db.commit()
                    db.refresh(step_record)
                    
                    # Update context with step result for next steps
                    context["previous_steps"][step_name] = step_result
                    total_cost += step_result.get("cost_est", 0.0)
                    
                    logger.info(
                        "step_completed",
                        run_id=run.id,
                        step=step_name,
                        tokens=step_result.get("tokens_used", 0),
                        cost=step_result.get("cost_est", 0.0),
                    )
                except Exception as e:
                    logger.error("step_failed", run_id=run.id, step=step_name, error=str(e))
                    # Save error step
                    error_step = AnalysisStep(
                        run_id=run.id,
                        step_name=step_name,
                        input_blob={"error": str(e)},
                        output_blob=f"Error: {str(e)}",
                    )
                    db.add(error_step)
                    db.commit()
                    # Continue with next step instead of failing completely
                    continue
            
            # Update run status
            run.status = RunStatus.SUCCEEDED
            run.finished_at = datetime.now(timezone.utc)
            run.cost_est_total = total_cost
            db.commit()
            
            logger.info("pipeline_completed", run_id=run.id, total_cost=total_cost)
            return run
            
        except Exception as e:
            logger.error("pipeline_failed", run_id=run.id, error=str(e))
            run.status = RunStatus.FAILED
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
            raise

