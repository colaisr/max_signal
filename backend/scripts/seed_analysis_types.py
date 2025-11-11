"""
Seed script to create default analysis types.
Run this after migrations to populate initial analysis types.
"""
from app.core.database import SessionLocal
from app.models.analysis_type import AnalysisType


def seed_analysis_types():
    """Create default analysis types."""
    db = SessionLocal()
    try:
        # Check if daystart already exists
        existing = db.query(AnalysisType).filter(AnalysisType.name == "daystart").first()
        if existing:
            print("Daystart analysis type already exists, skipping seed.")
            return
        
        daystart_config = {
            "steps": [
                {
                    "step_name": "wyckoff",
                    "step_type": "llm_analysis",
                    "model": "openai/gpt-4o-mini",
                    "system_prompt": "You are an expert in Wyckoff Method analysis. Analyze market structure to identify accumulation, distribution, markup, and markdown phases. Provide clear, actionable insights about market context and likely scenarios.",
                    "user_prompt_template": "Analyze {instrument} on {timeframe} timeframe using Wyckoff Method.\n\nRecent price action (last 20 candles):\n{market_data_summary}\n\nDetermine:\n1. Current Wyckoff phase (Accumulation/Distribution/Markup/Markdown)\n2. Market context and cycle position\n3. Likely scenario (continuation or reversal)\n4. Key levels to watch\n\nProvide analysis in structured format suitable for trading decisions.",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "data_sources": ["market_data"]
                },
                {
                    "step_name": "smc",
                    "step_type": "llm_analysis",
                    "model": "openai/gpt-4o-mini",
                    "system_prompt": "You are an expert in Smart Money Concepts (SMC). Analyze market structure to identify BOS (Break of Structure), CHoCH (Change of Character), Order Blocks, Fair Value Gaps (FVG), and Liquidity Pools. Identify key levels and liquidity events.",
                    "user_prompt_template": "Analyze {instrument} on {timeframe} using Smart Money Concepts.\n\nPrice structure (last 50 candles):\n{market_data_summary}\n\nIdentify:\n1. BOS (Break of Structure) and CHoCH points\n2. Order Blocks (OB) - supply/demand zones\n3. Fair Value Gaps (FVG) - imbalance zones\n4. Liquidity Pools - areas where stops are likely\n5. Key levels for potential price returns\n\nProvide structured analysis with specific price levels.",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "data_sources": ["market_data"]
                },
                {
                    "step_name": "vsa",
                    "step_type": "llm_analysis",
                    "model": "openai/gpt-4o-mini",
                    "system_prompt": "You are an expert in Volume Spread Analysis (VSA). Analyze volume, spread, and price action to identify large participant activity. Look for signals like no demand, no supply, stopping volume, climactic action, and effort vs result.",
                    "user_prompt_template": "Analyze {instrument} on {timeframe} using Volume Spread Analysis.\n\nOHLCV data (last 30 candles):\n{market_data_summary}\n\nIdentify:\n1. Large participant activity (volume analysis)\n2. No demand / no supply signals\n3. Stopping volume (absorption)\n4. Climactic action (exhaustion)\n5. Effort vs result (volume vs price movement)\n6. Areas where effort without result suggests reversal\n\nProvide VSA signals and their implications.",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "data_sources": ["market_data"]
                },
                {
                    "step_name": "delta",
                    "step_type": "llm_analysis",
                    "model": "openai/gpt-4o-mini",
                    "system_prompt": "You are an expert in Delta analysis. Analyze buying vs selling pressure to identify dominance, anomalous delta, absorption, divergence, and where large players are holding positions or absorbing aggression.",
                    "user_prompt_template": "Analyze {instrument} on {timeframe} using Delta analysis principles.\n\nNote: Full delta requires order flow data. Analyze buying/selling pressure from volume and price action.\n\nPrice and volume data (last 30 candles):\n{market_data_summary}\n\nIdentify:\n1. Buying vs selling dominance\n2. Anomalous delta patterns\n3. Absorption zones (volume without price movement)\n4. Divergences (price vs volume/strength)\n5. Where large players are holding or absorbing\n\nProvide delta-based insights.",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "data_sources": ["market_data"]
                },
                {
                    "step_name": "ict",
                    "step_type": "llm_analysis",
                    "model": "openai/gpt-4o-mini",
                    "system_prompt": "You are an expert in ICT (Inner Circle Trader) methodology. Analyze liquidity manipulation, PD Arrays (Premium/Discount), Fair Value Gaps, and optimal entry points after liquidity sweeps.",
                    "user_prompt_template": "Analyze {instrument} on {timeframe} using ICT methodology.\n\nPrice action (last 50 candles):\n{market_data_summary}\n\nPrevious analysis context:\n- Wyckoff phase: {wyckoff_output}\n- SMC structure: {smc_output}\n\nIdentify:\n1. Liquidity manipulation (sweeps above highs/below lows)\n2. PD Arrays (Premium/Discount zones)\n3. Fair Value Gaps (FVG) for return zones\n4. Optimal entry points after liquidity collection\n5. False breakouts and return scenarios\n\nProvide ICT-based entry strategy.",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "data_sources": ["market_data", "previous_steps"]
                },
                {
                    "step_name": "merge",
                    "step_type": "llm_analysis",
                    "model": "openai/gpt-4o-mini",
                    "system_prompt": "You are a professional trading analyst. Combine multiple analysis methods into a cohesive, actionable Telegram post. Follow the exact format and style specified in the user prompt. Write in Russian as specified.",
                    "user_prompt_template": "Объедини результаты анализа {instrument} на таймфрейме {timeframe} в единый пост для Telegram.\n\nРезультаты анализа по методам:\n\n1️⃣ WYCKOFF:\n{wyckoff_output}\n\n2️⃣ SMC (Smart Money Concepts):\n{smc_output}\n\n3️⃣ VSA (Volume Spread Analysis):\n{vsa_output}\n\n4️⃣ DELTA:\n{delta_output}\n\n5️⃣ ICT:\n{ict_output}\n\n---\n\nТеперь создай финальный пост в формате Telegram, следуя ТОЧНО шаблону из оригинального промпта (структурно, списками, без таблиц, с заголовком, внутридневным планом и тремя сценариями).",
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "data_sources": ["previous_steps"]
                }
            ],
            "default_instrument": "BTC/USDT",
            "default_timeframe": "H1",
            "estimated_cost": 0.18,
            "estimated_duration_seconds": 120
        }
        
        daystart = AnalysisType(
            name="daystart",
            display_name="Daystart Analysis",
            description="Full market analysis using 5 methodologies: Wyckoff, SMC, VSA, Delta, and ICT. Produces comprehensive Telegram-ready trading post.",
            version="1.0.0",
            config=daystart_config,
            is_active=1
        )
        
        db.add(daystart)
        db.commit()
        print("✅ Daystart analysis type created successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding analysis types: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_analysis_types()

