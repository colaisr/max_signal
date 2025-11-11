"""
OpenRouter LLM client for making AI calls.
"""
from openai import OpenAI
from app.core.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_LLM_MODEL
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for making LLM calls via OpenRouter."""
    
    def __init__(self):
        """Initialize OpenRouter client."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not configured in config_local.py")
        
        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
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
            logger.error("llm_call_failed", model=model, error=str(e))
            raise ValueError(f"LLM call failed: {str(e)}")

