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


def _normalize_futures_ticker(symbol: str) -> str:
    """Convert Bloomberg-style futures tickers to Yahoo Finance format.
    
    Maps common Bloomberg futures tickers to Yahoo Finance equivalents.
    Examples:
        NG1 -> NG=F (Natural Gas)
        B1! -> BZ=F (Brent Crude Oil)
        CL1 -> CL=F (WTI Crude Oil)
        GC1 -> GC=F (Gold)
        SI1 -> SI=F (Silver)
    """
    # Bloomberg to Yahoo Finance ticker mapping
    ticker_map = {
        'NG1': 'NG=F',      # Natural Gas
        'NG1!': 'NG=F',     # Natural Gas (continuous)
        'B1': 'BZ=F',       # Brent Crude Oil
        'B1!': 'BZ=F',      # Brent Crude Oil (continuous)
        'CL1': 'CL=F',      # WTI Crude Oil
        'CL1!': 'CL=F',     # WTI Crude Oil (continuous)
        'GC1': 'GC=F',      # Gold
        'GC1!': 'GC=F',     # Gold (continuous)
        'SI1': 'SI=F',      # Silver
        'SI1!': 'SI=F',     # Silver (continuous)
        'PL1': 'PL=F',      # Platinum
        'PL1!': 'PL=F',     # Platinum (continuous)
        'PA1': 'PA=F',      # Palladium
        'PA1!': 'PA=F',     # Palladium (continuous)
        'HO1': 'HO=F',      # Heating Oil
        'HO1!': 'HO=F',     # Heating Oil (continuous)
        'RB1': 'RB=F',      # RBOB Gasoline
        'RB1!': 'RB=F',     # RBOB Gasoline (continuous)
        'ZC1': 'ZC=F',      # Corn
        'ZC1!': 'ZC=F',     # Corn (continuous)
        'ZS1': 'ZS=F',      # Soybeans
        'ZS1!': 'ZS=F',     # Soybeans (continuous)
        'ZW1': 'ZW=F',      # Wheat
        'ZW1!': 'ZW=F',     # Wheat (continuous)
    }
    
    # Check if symbol needs mapping
    normalized = ticker_map.get(symbol.upper(), symbol)
    return normalized


def _get_display_name(symbol: str, type: str, exchange: str | None) -> str:
    """Generate display name for instrument."""
    if type == "crypto":
        # For crypto, show symbol as-is (e.g., "BTC/USDT")
        return symbol.replace("/", " / ")
    else:
        # For equities, try to make it readable
        # Map Bloomberg-style futures to readable names
        display_map = {
            'NG=F': 'Natural Gas Futures',
            'NG1': 'Natural Gas Futures',
            'NG1!': 'Natural Gas Futures',
            'BZ=F': 'Brent Crude Oil Futures',
            'B1': 'Brent Crude Oil Futures',
            'B1!': 'Brent Crude Oil Futures',
            'CL=F': 'WTI Crude Oil Futures',
            'GC=F': 'Gold Futures',
            'SI=F': 'Silver Futures',
        }
        return display_map.get(symbol.upper(), symbol)


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


def _get_all_moex_instruments() -> List[str]:
    """Get all available MOEX instruments from MOEX ISS API.
    
    Returns list of tickers (e.g., ['SBER', 'GAZP', 'ROSN']).
    Uses MOEX ISS API which is free and public.
    """
    try:
        import requests
        import apimoex
        
        with requests.Session() as session:
            # Get securities from main trading board (TQBR - T+2 stocks)
            data = apimoex.get_board_securities(session, board='TQBR')
            
            # Extract tickers
            tickers = sorted(set(sec.get('SECID') for sec in data if sec.get('SECID')))
            
            logger.info(f"Fetched {len(tickers)} MOEX instruments from ISS API")
            return tickers
            
    except ImportError:
        logger.warning("apimoex package not installed. MOEX instruments will not be available.")
        logger.warning("Install with: pip install apimoex")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch MOEX instruments from ISS API: {e}")
        return []


def _get_all_equity_instruments() -> List[str]:
    """Get comprehensive list of equity instruments.
    
    Note: yfinance doesn't provide a list API, so we use a curated list
    of popular stocks, ETFs, indices, and commodity futures.
    MOEX instruments are fetched separately from MOEX ISS API.
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
    
    # Commodity futures (Yahoo Finance =F suffix and Bloomberg-style tickers)
    # Note: Bloomberg-style tickers (NG1, B1!, etc.) will be mapped to Yahoo Finance equivalents
    commodity_futures = [
        # Energy
        "CL=F",  # WTI Crude Oil
        "CL1",   # WTI Crude Oil (Bloomberg style)
        "CL1!",  # WTI Crude Oil (continuous)
        "BZ=F",  # Brent Crude Oil
        "B1",    # Brent Crude Oil (Bloomberg style)
        "B1!",   # Brent Crude Oil (continuous)
        "NG=F",  # Henry Hub Natural Gas
        "NG1",   # Natural Gas (Bloomberg style)
        "NG1!",  # Natural Gas (continuous)
        "HO=F",  # Heating Oil
        "HO1",   # Heating Oil (Bloomberg style)
        "HO1!",  # Heating Oil (continuous)
        "RB=F",  # RBOB Gasoline
        "RB1",   # RBOB Gasoline (Bloomberg style)
        "RB1!",  # RBOB Gasoline (continuous)
        # Metals
        "GC=F",  # Gold
        "GC1",   # Gold (Bloomberg style)
        "GC1!",  # Gold (continuous)
        "SI=F",  # Silver
        "SI1",   # Silver (Bloomberg style)
        "SI1!",  # Silver (continuous)
        "PL=F",  # Platinum
        "PL1",   # Platinum (Bloomberg style)
        "PL1!",  # Platinum (continuous)
        "PA=F",  # Palladium
        "PA1",   # Palladium (Bloomberg style)
        "PA1!",  # Palladium (continuous)
        # Agriculture
        "ZC=F",  # Corn
        "ZC1",   # Corn (Bloomberg style)
        "ZC1!",  # Corn (continuous)
        "ZS=F",  # Soybeans
        "ZS1",   # Soybeans (Bloomberg style)
        "ZS1!",  # Soybeans (continuous)
        "ZW=F",  # Wheat
        "ZW1",   # Wheat (Bloomberg style)
        "ZW1!",  # Wheat (continuous)
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
    - Comprehensive list of equities (stocks, ETFs, indices, commodity futures)
    - All MOEX instruments from MOEX ISS API (dynamically fetched)
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
    
    # Add equity instruments (US stocks, ETFs, commodity futures)
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
    
    # Add MOEX instruments (dynamically fetched from MOEX ISS API)
    moex_symbols = _get_all_moex_instruments()
    for symbol in moex_symbols:
        db_inst = db_instruments_map.get(symbol)
        result.append(InstrumentWithStatusResponse(
            symbol=symbol,
            type="equity",  # MOEX stocks are also equities
            exchange="MOEX",
            display_name=_get_display_name(symbol, "equity", "MOEX"),
            is_enabled=db_inst.is_enabled if db_inst else False,  # Default to disabled (admin must enable)
            id=db_inst.id if db_inst else None
        ))
    
    # Sort by type, then exchange, then symbol
    result.sort(key=lambda x: (x.type, x.exchange or "", x.symbol))
    
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
        # Check if it's a MOEX instrument (from MOEX ISS API list)
        moex_symbols = _get_all_moex_instruments()
        is_moex = symbol in moex_symbols
        
        if is_moex:
            inst_type = "equity"
            exchange = "MOEX"
        elif "/" in symbol.upper() or symbol.upper().endswith('USDT'):
            inst_type = "crypto"
            exchange = "binance"
        else:
            inst_type = "equity"
            exchange = None  # Will be determined when data is fetched
        
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

