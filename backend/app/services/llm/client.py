"""
OpenRouter LLM client for making AI calls.
"""
from openai import OpenAI
from app.core.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_LLM_MODEL
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def get_openrouter_api_key(db: Optional[Session] = None) -> Optional[str]:
    """Get OpenRouter API key from Settings or config_local.py.
    
    Priority:
    1. AppSettings table (if db provided)
    2. config_local.py (fallback)
    
    Returns:
        API key string or None if not found
    """
    # Try Settings first if DB session provided
    if db:
        try:
            from app.models.settings import AppSettings
            setting = db.query(AppSettings).filter(
                AppSettings.key == "openrouter_api_key"
            ).first()
            if setting and setting.value:
                return setting.value
        except Exception as e:
            logger.warning(f"Failed to read OpenRouter API key from Settings: {e}")
    
    # Fallback to config_local.py
    if OPENROUTER_API_KEY:
        return OPENROUTER_API_KEY
    
    return None


class LLMClient:
    """Client for making LLM calls via OpenRouter."""
    
    def __init__(self, api_key: Optional[str] = None, db: Optional[Session] = None):
        """Initialize OpenRouter client.
        
        Args:
            api_key: Optional API key. If not provided, will try to get from Settings or config_local.py
            db: Optional database session to read from AppSettings
        """
        # Get API key: use provided, or fetch from Settings/config
        if not api_key:
            api_key = get_openrouter_api_key(db)
        
        if not api_key:
            raise ValueError(
                "OpenRouter API key not configured. "
                "Please set it in Settings (Settings page) or config_local.py"
            )
        
        self.api_key = api_key
        self.client = OpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
        )
        self.default_model = DEFAULT_LLM_MODEL
    
    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Make an LLM call via OpenRouter.
        
        Args:
            system_prompt: System message/instructions
            user_prompt: User message/content
            model: Model to use (defaults to DEFAULT_LLM_MODEL)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dict with 'content', 'model', 'tokens_used', 'cost_est'
        """
        model = model or self.default_model
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Estimate cost (rough approximation, varies by model)
            # OpenRouter pricing: https://openrouter.ai/models
            # Using conservative estimate of $0.01 per 1K tokens for most models
            cost_est = (tokens_used / 1000) * 0.01
            
            logger.info(
                "llm_call_completed",
                model=model,
                tokens=tokens_used,
                cost_est=cost_est,
            )
            
            return {
                "content": content,
                "model": model,
                "tokens_used": tokens_used,
                "cost_est": cost_est,
            }
        except Exception as e:
            error_msg = str(e)
            logger.error("llm_call_failed", model=model, error=error_msg)
            
            # Check if it's an authentication error (invalid API key)
            if "401" in error_msg or "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
                raise ValueError(
                    f"OpenRouter API key is invalid or expired. "
                    f"Please update it in Settings (Settings page). Error: {error_msg}"
                )
            
            raise ValueError(f"LLM call failed: {error_msg}")

