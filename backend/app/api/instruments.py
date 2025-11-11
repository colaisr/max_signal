"""
Instruments endpoints.
"""
from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter()


class InstrumentResponse(BaseModel):
    """Instrument response model."""
    symbol: str
    type: str  # "crypto" or "equity"
    exchange: str
    display_name: str


@router.get("", response_model=List[InstrumentResponse])
async def list_instruments():
    """List available instruments."""
    # Predefined list of popular instruments
    instruments = [
        # Crypto
        {"symbol": "BTC/USDT", "type": "crypto", "exchange": "binance", "display_name": "Bitcoin / USDT"},
        {"symbol": "ETH/USDT", "type": "crypto", "exchange": "binance", "display_name": "Ethereum / USDT"},
        {"symbol": "BNB/USDT", "type": "crypto", "exchange": "binance", "display_name": "BNB / USDT"},
        {"symbol": "SOL/USDT", "type": "crypto", "exchange": "binance", "display_name": "Solana / USDT"},
        {"symbol": "ADA/USDT", "type": "crypto", "exchange": "binance", "display_name": "Cardano / USDT"},
        # Equities
        {"symbol": "AAPL", "type": "equity", "exchange": "NASDAQ", "display_name": "Apple Inc."},
        {"symbol": "TSLA", "type": "equity", "exchange": "NASDAQ", "display_name": "Tesla Inc."},
        {"symbol": "MSFT", "type": "equity", "exchange": "NASDAQ", "display_name": "Microsoft Corporation"},
        {"symbol": "GOOGL", "type": "equity", "exchange": "NASDAQ", "display_name": "Alphabet Inc."},
        {"symbol": "AMZN", "type": "equity", "exchange": "NASDAQ", "display_name": "Amazon.com Inc."},
        {"symbol": "NVDA", "type": "equity", "exchange": "NASDAQ", "display_name": "NVIDIA Corporation"},
        {"symbol": "SPY", "type": "equity", "exchange": "NYSE", "display_name": "SPDR S&P 500 ETF"},
    ]
    
    return [InstrumentResponse(**inst) for inst in instruments]

