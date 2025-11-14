"""
Analysis pipeline orchestrator.
Runs the Daystart analysis through all steps: Wyckoff, SMC, VSA, Delta, ICT, Merge.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
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
    PriceActionAnalyzer,
    MergeAnalyzer,
)
import logging

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Orchestrates the complete analysis pipeline."""
    
    def __init__(self):
        self.data_service = None  # Will be initialized in run() with db session to get Tinkoff token
        self.llm_client = None  # Will be initialized in run() with db session
        self.steps = [
            ("wyckoff", WyckoffAnalyzer()),
            ("smc", SMCAnalyzer()),
            ("vsa", VSAAnalyzer()),
            ("delta", DeltaAnalyzer()),
            ("ict", ICTAnalyzer()),
            ("price_action", PriceActionAnalyzer()),
            ("merge", MergeAnalyzer()),
        ]
    
    def run(
        self,
        run: AnalysisRun,
        db: Session,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisRun:
        """Execute the complete analysis pipeline.
        
        Args:
            run: AnalysisRun database record
            db: Database session
            
        Returns:
            Updated AnalysisRun with all steps completed
        """
        try:
            # Initialize LLM client with db session to read API key from Settings
            if not self.llm_client:
                self.llm_client = LLMClient(db=db)
            
            # Initialize DataService with db session to read Tinkoff token from Settings
            if not self.data_service:
                from app.services.data.adapters import DataService
                self.data_service = DataService(db=db)
            
            # Update status to running
            run.status = RunStatus.RUNNING
            db.commit()
            
            # Fetch market data
            logger.info(f"fetching_market_data: run_id={run.id}, instrument={run.instrument.symbol}")
            market_data = self.data_service.fetch_market_data(
                instrument=run.instrument.symbol,
                timeframe=run.timeframe,
                use_cache=True
            )
            
            # Get configuration: use custom_config if provided, otherwise use analysis_type.config
            config = custom_config
            if not config and run.analysis_type:
                config = run.analysis_type.config
            
            if not config:
                raise ValueError("No configuration available for analysis run")
            
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
                logger.info(f"running_step: run_id={run.id}, step={step_name}")
                
                # Find step configuration
                step_config = None
                if config and "steps" in config:
                    step_config = next(
                        (s for s in config["steps"] if s.get("step_name") == step_name),
                        None
                    )
                
                try:
                    # Run the step (sync call) with step configuration
                    step_result = analyzer.analyze(
                        context=context,
                        llm_client=self.llm_client,
                        step_config=step_config,
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
                        f"step_completed: run_id={run.id}, step={step_name}, "
                        f"tokens={step_result.get('tokens_used', 0)}, cost={step_result.get('cost_est', 0.0)}"
                    )
                except Exception as e:
                    logger.error(f"step_failed: run_id={run.id}, step={step_name}, error={str(e)}")
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
            
            logger.info(f"pipeline_completed: run_id={run.id}, total_cost={total_cost}")
            return run
            
        except Exception as e:
            logger.error(f"pipeline_failed: run_id={run.id}, error={str(e)}")
            run.status = RunStatus.FAILED
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
            raise

