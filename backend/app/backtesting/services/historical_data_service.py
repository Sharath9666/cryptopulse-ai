"""
Historical data fetching service.
Fetches public OHLCV candle bars from the Binance public API.
"""

from datetime import datetime, timezone
import httpx
from typing import List
from loguru import logger

from app.backtesting.models.historical_candle import HistoricalCandle


class HistoricalDataService:
    """
    Downloads historical market candles in chunks, converting them to Pydantic objects.
    """
    def __init__(self) -> None:
        self.base_url = "https://api.binance.com/api/v3/klines"

    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[HistoricalCandle]:
        """
        Queries Binance REST API to load OHLCV data within the requested timeframe.
        """
        symbol_upper = symbol.upper()
        
        # Convert start/end datetimes to UTC timestamps in milliseconds
        start_ms = int(start_date.replace(tzinfo=timezone.utc).timestamp() * 1000)
        end_ms = int(end_date.replace(tzinfo=timezone.utc).timestamp() * 1000)

        candles: List[HistoricalCandle] = []
        current_start = start_ms

        logger.info(
            f"Downloading historical candles for {symbol_upper} ({timeframe}) "
            f"from {start_date} to {end_date}..."
        )

        async with httpx.AsyncClient() as client:
            while current_start < end_ms:
                params = {
                    "symbol": symbol_upper,
                    "interval": timeframe,
                    "startTime": current_start,
                    "endTime": end_ms,
                    "limit": 1000
                }

                try:
                    response = await client.get(self.base_url, params=params, timeout=15.0)
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data:
                        break

                    for item in data:
                        # Extract OHLCV elements
                        # kline fields: [OpenTime, Open, High, Low, Close, Volume, CloseTime, ...]
                        open_time_ms = int(item[0])
                        close_time_ms = int(item[6])
                        
                        candle = HistoricalCandle(
                            symbol=symbol_upper,
                            timeframe=timeframe,
                            open=float(item[1]),
                            high=float(item[2]),
                            low=float(item[3]),
                            close=float(item[4]),
                            volume=float(item[5]),
                            start_time=datetime.fromtimestamp(open_time_ms / 1000.0, tz=timezone.utc),
                            end_time=datetime.fromtimestamp(close_time_ms / 1000.0, tz=timezone.utc)
                        )
                        candles.append(candle)

                    # Update start point for next loop (close time of last candle + 1ms)
                    last_open_time = int(data[-1][0])
                    if last_open_time <= current_start:
                        # Prevent infinite loop if API returns same start point
                        break
                    current_start = last_open_time + 1
                    
                    logger.info(f"Retrieved {len(data)} candles. Progressive total: {len(candles)}")
                except Exception as e:
                    logger.error(f"Error downloading klines batch from Binance: {e}")
                    break

        logger.info(f"Historical download finished. Total candle count loaded: {len(candles)}")
        return candles
