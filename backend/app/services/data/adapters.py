"""
Data adapters for fetching market data from various sources.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import ccxt
import yfinance as yf
import pandas as pd
from app.core.database import SessionLocal
from app.models.data_cache import DataCache
from app.services.data.normalized import MarketData, OHLCVCandle
import json
import hashlib


class DataAdapter:
    """Base class for data adapters."""
    
    def fetch_ohlcv(
        self,
        instrument: str,
        timeframe: str,
        limit: int = 500,
        since: Optional[datetime] = None
    ) -> MarketData:
        """Fetch OHLCV data. Must be implemented by subclasses."""
        raise NotImplementedError


class CCXTAdapter(DataAdapter):
    """CCXT adapter for crypto exchanges."""
    
    def __init__(self, exchange_name: str = "binance"):
        """Initialize CCXT adapter.
        
        Args:
            exchange_name: Exchange name (binance, coinbase, etc.)
        """
        exchange_class = getattr(ccxt, exchange_name)
        self.exchange = exchange_class({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # or 'future'
            }
        })
        self.exchange_name = exchange_name
    
    def _normalize_timeframe(self, timeframe: str) -> str:
        """Convert our timeframe to CCXT format."""
        mapping = {
            'M1': '1m',
            'M5': '5m',
            'M15': '15m',
            'M30': '30m',
            'H1': '1h',
            'H4': '4h',
            'D1': '1d',
        }
        return mapping.get(timeframe.upper(), timeframe.lower())
    
    def fetch_ohlcv(
        self,
        instrument: str,
        timeframe: str,
        limit: int = 500,
        since: Optional[datetime] = None
    ) -> MarketData:
        """Fetch OHLCV data from crypto exchange."""
        # Normalize symbol format (ensure it matches exchange format)
        symbol = instrument.upper()
        if '/' not in symbol:
            # Try to add /USDT if not present
            symbol = f"{symbol}/USDT"
        
        ccxt_timeframe = self._normalize_timeframe(timeframe)
        since_timestamp = int(since.timestamp() * 1000) if since else None
        
        try:
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(
                symbol,
                ccxt_timeframe,
                since=since_timestamp,
                limit=limit
            )
            
            # Convert to normalized format
            candles = []
            for candle in ohlcv:
                candles.append(OHLCVCandle(
                    timestamp=datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc),
                    open=candle[1],
                    high=candle[2],
                    low=candle[3],
                    close=candle[4],
                    volume=candle[5]
                ))
            
            return MarketData(
                instrument=instrument,
                timeframe=timeframe,
                exchange=self.exchange_name,
                candles=candles,
                fetched_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            raise ValueError(f"Failed to fetch data from {self.exchange_name}: {str(e)}")


class YFinanceAdapter(DataAdapter):
    """yfinance adapter for equities."""
    
    def _normalize_timeframe(self, timeframe: str) -> str:
        """Convert our timeframe to yfinance interval."""
        mapping = {
            'M1': '1m',
            'M5': '5m',
            'M15': '15m',
            'M30': '30m',
            'H1': '1h',
            'D1': '1d',
        }
        return mapping.get(timeframe.upper(), '1d')
    
    def fetch_ohlcv(
        self,
        instrument: str,
        timeframe: str,
        limit: int = 500,
        since: Optional[datetime] = None
    ) -> MarketData:
        """Fetch OHLCV data from yfinance."""
        ticker = yf.Ticker(instrument)
        interval = self._normalize_timeframe(timeframe)
        
        # Calculate period
        if since:
            period = None
            end_date = datetime.utcnow()
        else:
            # Default period based on timeframe
            if timeframe in ['M1', 'M5', 'M15', 'M30', 'H1']:
                period = '5d'  # Intraday data
            else:
                period = '1mo'  # Daily data
        
        try:
            # Fetch data
            if since:
                df = ticker.history(
                    start=since,
                    end=datetime.utcnow(),
                    interval=interval
                )
            else:
                df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                raise ValueError(f"No data available for {instrument}")
            
            # Limit results
            df = df.tail(limit)
            
            # Convert to normalized format
            candles = []
            for idx, row in df.iterrows():
                candles.append(OHLCVCandle(
                    timestamp=idx.to_pydatetime() if isinstance(idx, pd.Timestamp) else idx,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=float(row['Volume'])
                ))
            
            return MarketData(
                instrument=instrument,
                timeframe=timeframe,
                exchange='yfinance',
                candles=candles,
                fetched_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            raise ValueError(f"Failed to fetch data from yfinance: {str(e)}")


class DataService:
    """Service for fetching and caching market data."""
    
    def __init__(self):
        self.ccxt_adapter = CCXTAdapter()
        self.yfinance_adapter = YFinanceAdapter()
    
    def _get_cache_key(self, instrument: str, timeframe: str) -> str:
        """Generate cache key."""
        key = f"{instrument}:{timeframe}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cached_data(self, cache_key: str, ttl_seconds: int = 300) -> Optional[MarketData]:
        """Get cached data if still valid."""
        db = SessionLocal()
        try:
            cache_entry = db.query(DataCache).filter(DataCache.key == cache_key).first()
            if cache_entry:
                age = (datetime.now(timezone.utc) - cache_entry.fetched_at.replace(tzinfo=timezone.utc)).total_seconds()
                if age < min(cache_entry.ttl_seconds, ttl_seconds):
                    # Return cached data
                    data_dict = json.loads(cache_entry.payload)
                    # Convert datetime strings back to datetime objects
                    data_dict['fetched_at'] = datetime.fromisoformat(data_dict['fetched_at'])
                    for candle in data_dict['candles']:
                        candle['timestamp'] = datetime.fromisoformat(candle['timestamp'])
                    return MarketData(**data_dict)
            return None
        finally:
            db.close()
    
    def _cache_data(self, cache_key: str, data: MarketData, ttl_seconds: int = 300):
        """Cache market data."""
        db = SessionLocal()
        try:
            # Convert to JSON-serializable format
            data_dict = {
                'instrument': data.instrument,
                'timeframe': data.timeframe,
                'exchange': data.exchange,
                'candles': [
                    {
                        'timestamp': c.timestamp.isoformat(),
                        'open': c.open,
                        'high': c.high,
                        'low': c.low,
                        'close': c.close,
                        'volume': c.volume
                    }
                    for c in data.candles
                ],
                'fetched_at': data.fetched_at.isoformat()
            }
            
            # Update or create cache entry
            cache_entry = db.query(DataCache).filter(DataCache.key == cache_key).first()
            if cache_entry:
                cache_entry.payload = json.dumps(data_dict)
                cache_entry.fetched_at = datetime.now(timezone.utc)
                cache_entry.ttl_seconds = ttl_seconds
            else:
                cache_entry = DataCache(
                    key=cache_key,
                    payload=json.dumps(data_dict),
                    ttl_seconds=ttl_seconds
                )
                db.add(cache_entry)
            
            db.commit()
        finally:
            db.close()
    
    def fetch_market_data(
        self,
        instrument: str,
        timeframe: str,
        use_cache: bool = True,
        cache_ttl: int = 300
    ) -> MarketData:
        """Fetch market data with caching support.
        
        Args:
            instrument: Symbol (e.g., 'BTC/USDT', 'AAPL')
            timeframe: Timeframe (M1, M5, M15, H1, D1, etc.)
            use_cache: Whether to use cache
            cache_ttl: Cache TTL in seconds (default 5 minutes)
        """
        cache_key = self._get_cache_key(instrument, timeframe)
        
        # Try cache first
        if use_cache:
            cached = self._get_cached_data(cache_key, cache_ttl)
            if cached:
                return cached
        
        # Determine adapter based on instrument type
        if '/' in instrument.upper() or instrument.upper().endswith('USDT'):
            # Crypto
            adapter = self.ccxt_adapter
        else:
            # Equity
            adapter = self.yfinance_adapter
        
        # Fetch data
        data = adapter.fetch_ohlcv(instrument, timeframe, limit=500)
        
        # Cache it
        if use_cache:
            self._cache_data(cache_key, data, cache_ttl)
        
        return data

