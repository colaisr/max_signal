"""
Instruments endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Set, Dict
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.instrument import Instrument
import ccxt
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class InstrumentResponse(BaseModel):
    """Instrument response model."""
    symbol: str
    type: str  # "crypto" or "equity"
    exchange: str | None
    display_name: str


class InstrumentWithStatusResponse(BaseModel):
    """Instrument with enabled status response model."""
    symbol: str
    type: str  # "crypto" or "equity"
    exchange: str | None
    display_name: str
    is_enabled: bool
    id: int | None = None  # Database ID if exists


class ToggleInstrumentRequest(BaseModel):
    """Request model for toggling instrument enabled status."""
    symbol: str


def _get_display_name(symbol: str, type: str, exchange: str | None) -> str:
    """Generate display name for instrument."""
    if type == "crypto":
        # For crypto, show symbol as-is (e.g., "BTC/USDT")
        return symbol.replace("/", " / ")
    else:
        # For equities, try to make it readable
        # Could be enhanced with a mapping of common tickers
        return symbol


def _get_predefined_instruments() -> List[Dict]:
    """Get predefined list of popular instruments."""
    return [
        # Crypto
        {"symbol": "BTC/USDT", "type": "crypto", "exchange": "binance", "display_name": "Bitcoin / USDT"},
        {"symbol": "ETH/USDT", "type": "crypto", "exchange": "binance", "display_name": "Ethereum / USDT"},
        {"symbol": "BNB/USDT", "type": "crypto", "exchange": "binance", "display_name": "BNB / USDT"},
        {"symbol": "SOL/USDT", "type": "crypto", "exchange": "binance", "display_name": "Solana / USDT"},
        {"symbol": "ADA/USDT", "type": "crypto", "exchange": "binance", "display_name": "Cardano / USDT"},
        {"symbol": "XRP/USDT", "type": "crypto", "exchange": "binance", "display_name": "Ripple / USDT"},
        {"symbol": "DOGE/USDT", "type": "crypto", "exchange": "binance", "display_name": "Dogecoin / USDT"},
        {"symbol": "MATIC/USDT", "type": "crypto", "exchange": "binance", "display_name": "Polygon / USDT"},
        {"symbol": "AVAX/USDT", "type": "crypto", "exchange": "binance", "display_name": "Avalanche / USDT"},
        {"symbol": "DOT/USDT", "type": "crypto", "exchange": "binance", "display_name": "Polkadot / USDT"},
        # Equities
        {"symbol": "AAPL", "type": "equity", "exchange": "NASDAQ", "display_name": "Apple Inc."},
        {"symbol": "TSLA", "type": "equity", "exchange": "NASDAQ", "display_name": "Tesla Inc."},
        {"symbol": "MSFT", "type": "equity", "exchange": "NASDAQ", "display_name": "Microsoft Corporation"},
        {"symbol": "GOOGL", "type": "equity", "exchange": "NASDAQ", "display_name": "Alphabet Inc."},
        {"symbol": "AMZN", "type": "equity", "exchange": "NASDAQ", "display_name": "Amazon.com Inc."},
        {"symbol": "NVDA", "type": "equity", "exchange": "NASDAQ", "display_name": "NVIDIA Corporation"},
        {"symbol": "META", "type": "equity", "exchange": "NASDAQ", "display_name": "Meta Platforms Inc."},
        {"symbol": "SPY", "type": "equity", "exchange": "NYSE", "display_name": "SPDR S&P 500 ETF"},
        {"symbol": "QQQ", "type": "equity", "exchange": "NASDAQ", "display_name": "Invesco QQQ Trust"},
        {"symbol": "DIA", "type": "equity", "exchange": "NYSE", "display_name": "SPDR Dow Jones ETF"},
    ]


def _get_all_crypto_instruments() -> List[str]:
    """Get all available crypto instruments from CCXT (Binance)."""
    try:
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        markets = exchange.load_markets()
        # Filter for USDT pairs only
        usdt_pairs = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')]
        return sorted(usdt_pairs)
    except Exception as e:
        logger.error(f"Failed to fetch crypto instruments from CCXT: {e}")
        return []


def _get_all_equity_instruments() -> List[str]:
    """Get comprehensive list of equity instruments.
    
    Note: yfinance doesn't provide a list API, so we use a curated list
    of popular stocks, ETFs, indices, and commodity futures.
    MOEX (.ME) tickers are excluded as they often return no data from yfinance.
    """
    # Popular stocks (S&P 500 top companies + major tech)
    stocks = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "V", "JNJ",
        "WMT", "JPM", "MA", "PG", "UNH", "HD", "DIS", "BAC", "ADBE", "CRM",
        "VZ", "CMCSA", "NFLX", "COST", "PEP", "AVGO", "TMO", "ABT", "CSCO", "ACN",
        "NKE", "MRK", "TXN", "LIN", "DHR", "QCOM", "PM", "HON", "INTU", "AMGN",
        "AMD", "ISRG", "RTX", "AMAT", "LOW", "GE", "BKNG", "ADP", "SBUX", "TJX",
        "AXP", "GILD", "MDT", "C", "BLK", "DE", "ADI", "ZTS", "REGN", "MMC",
        "APH", "ITW", "ETN", "TGT", "SCHW", "BSX", "KLAC", "SNPS", "CDNS", "FTNT",
        "MCHP", "NXPI", "CTSH", "ANSS", "WDAY", "PAYX", "CTAS", "FAST", "IDXX", "ODFL"
    ]
    
    # Major ETFs
    etfs = [
        "SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "VEA", "VWO", "AGG", "BND",
        "GLD", "SLV", "USO", "TLT", "HYG", "LQD", "EFA", "EEM", "IEFA", "IEMG",
        "VTV", "VUG", "VYM", "VXUS", "BNDX", "VGK", "VPL", "VSS", "VXF", "VB"
    ]
    
    # Indices (as ETFs)
    indices = ["SPY", "QQQ", "DIA", "IWM", "VIX"]
    
    # Commodity futures (Yahoo Finance =F suffix)
    commodity_futures = [
        "CL=F",  # WTI Crude Oil
        "BZ=F",  # Brent Crude Oil
        "NG=F",  # Henry Hub Natural Gas
        "GC=F",  # Gold
        "SI=F",  # Silver
        "PL=F",  # Platinum
        "PA=F",  # Palladium
    ]
    
    # Combine and deduplicate
    # Note: We intentionally exclude some regional/forex tickers with frequent availability issues on yfinance
    # to avoid user-facing errors (e.g., many .ME tickers and RUB pairs often return no data).
    all_equities = list(set(stocks + etfs + indices + commodity_futures))
    return sorted(all_equities)


@router.get("", response_model=List[InstrumentResponse])
async def list_instruments(db: Session = Depends(get_db)):
    """List enabled instruments for use in dropdowns.
    
    Returns only instruments that are explicitly enabled (is_enabled=True) in the database.
    All instruments are disabled by default - admin must enable them in Settings.
    """
    # Get only enabled instruments from database
    db_instruments = db.query(Instrument).filter(Instrument.is_enabled == True).all()
    
    # Convert to response format
    result = []
    for db_inst in db_instruments:
        result.append({
            "symbol": db_inst.symbol,
            "type": db_inst.type,
            "exchange": db_inst.exchange,
            "display_name": _get_display_name(db_inst.symbol, db_inst.type, db_inst.exchange)
        })
    
    # Sort alphabetically
    result.sort(key=lambda x: x["symbol"])
    
    return [InstrumentResponse(**inst) for inst in result]


@router.get("/all", response_model=List[InstrumentWithStatusResponse])
async def list_all_instruments(db: Session = Depends(get_db)):
    """List all available instruments with their enabled status.
    
    This endpoint is used in the Settings page to manage which instruments
    appear in dropdowns. It includes:
    - All crypto pairs from CCXT (Binance USDT pairs)
    - Comprehensive list of equities (stocks, ETFs, indices)
    - Current enabled status from database
    """
    # Get all instruments from database
    db_instruments = db.query(Instrument).all()
    db_instruments_map: Dict[str, Instrument] = {inst.symbol: inst for inst in db_instruments}
    
    result = []
    
    # Add crypto instruments
    crypto_symbols = _get_all_crypto_instruments()
    for symbol in crypto_symbols:
        db_inst = db_instruments_map.get(symbol)
        result.append(InstrumentWithStatusResponse(
            symbol=symbol,
            type="crypto",
            exchange="binance",
            display_name=_get_display_name(symbol, "crypto", "binance"),
            is_enabled=db_inst.is_enabled if db_inst else False,  # Default to disabled (admin must enable)
            id=db_inst.id if db_inst else None
        ))
    
    # Add equity instruments
    equity_symbols = _get_all_equity_instruments()
    for symbol in equity_symbols:
        db_inst = db_instruments_map.get(symbol)
        result.append(InstrumentWithStatusResponse(
            symbol=symbol,
            type="equity",
            exchange="NASDAQ" if symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"] else "NYSE",
            display_name=_get_display_name(symbol, "equity", None),
            is_enabled=db_inst.is_enabled if db_inst else False,  # Default to disabled (admin must enable)
            id=db_inst.id if db_inst else None
        ))
    
    # Sort by type, then symbol
    result.sort(key=lambda x: (x.type, x.symbol))
    
    return result


@router.put("/toggle", response_model=InstrumentWithStatusResponse)
async def toggle_instrument(request: ToggleInstrumentRequest, db: Session = Depends(get_db)):
    """Toggle enabled status of an instrument.
    
    Creates the instrument in database if it doesn't exist.
    
    Args:
        request: Request body containing the instrument symbol
    """
    symbol = request.symbol
    # Find or create instrument
    instrument = db.query(Instrument).filter(Instrument.symbol == symbol).first()
    
    if not instrument:
        # Determine type and exchange
        inst_type = "crypto" if "/" in symbol.upper() else "equity"
        exchange = "binance" if inst_type == "crypto" else None
        
        # Create new instrument - if user is toggling, they want it enabled
        instrument = Instrument(
            symbol=symbol,
            type=inst_type,
            exchange=exchange,
            is_enabled=True  # User clicked toggle to enable, so create as enabled
        )
        db.add(instrument)
    else:
        # Toggle enabled status
        instrument.is_enabled = not instrument.is_enabled
    
    db.commit()
    db.refresh(instrument)
    
    return InstrumentWithStatusResponse(
        symbol=instrument.symbol,
        type=instrument.type,
        exchange=instrument.exchange,
        display_name=_get_display_name(instrument.symbol, instrument.type, instrument.exchange),
        is_enabled=instrument.is_enabled,
        id=instrument.id
    )

