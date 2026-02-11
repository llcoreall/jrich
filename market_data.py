import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

class MarketData:
    """
    Handles data fetching from yfinance for assets and currencies.
    Implements caching/freshness logic.
    """
    def __init__(self):
        self._price_cache = {}
        self._info_cache = {}
        self._fx_cache = {}
        self._fx_last_update = None
        self.FX_FRESHNESS_LIMIT = 3600  # 1 hour in seconds

    def get_asset_info(self, ticker: str):
        """
        Fetches basic info for a ticker to determine Sector and Asset Class.
        """
        if ticker in self._info_cache:
            return self._info_cache[ticker]

        try:
            # Optimize: use Ticker.fast_info for price if possible, but we need sector
            # .info is slower but necessary for sector
            t = yf.Ticker(ticker)
            info = t.info
            
            # Determine Asset Class and Sector
            # Determine Asset Class and Sector
            quote_type = info.get('quoteType', '').upper()
            
            # 1. Asset Class Determination
            asset_class = 'Stock' # Default
            if quote_type == 'CRYPTOCURRENCY':
                asset_class = 'Crypto'
            elif quote_type == 'ETF' or quote_type == 'MUTUALFUND':
                asset_class = 'ETF'
            elif quote_type == 'FUTURE':
                asset_class = 'Future'
            elif quote_type == 'INDEX':
                asset_class = 'Index'
            elif quote_type == 'EQUITY':
                asset_class = 'Stock'
                
            # 2. Sector Determination
            # ETFs often have 'category' instead of 'sector', or nothing.
            sector = info.get('sector')
            if not sector:
                sector = info.get('category')
            if not sector and asset_class == 'ETF':
                sector = "Exchange Traded Fund" # Default for ETFs if no category
            if not sector:
                sector = "Unknown"
            
            # Fallback for common Crypto tickers if yfinance doesn't explicitly label them nicely
            if ticker.endswith('-USD'):
                asset_class = 'Crypto'
                sector = 'Crypto'

            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            previous_close = info.get('previousClose', 0.0)

            data = {
                'price': current_price,
                'previous_close': previous_close,
                'sector': sector,
                'asset_class': asset_class,
                'name': info.get('shortName', ticker)
            }
            self._info_cache[ticker] = data
            return data
        except Exception as e:
            print(f"Error fetching info for {ticker}: {e}")
            return None

    def get_current_price(self, ticker: str) -> float:
        """Gets real-time price. Uses fast_info for speed."""
        try:
            t = yf.Ticker(ticker)
            # fast_info is much faster than .info
            price = t.fast_info.last_price
            if price is None:
                # Fallback
                info = self.get_asset_info(ticker)
                price = info['price'] if info else 0.0
            return price
        except Exception:
            return 0.0

    def get_fx_rates(self, base_currency="USD") -> dict:
        """
        Returns dictionary of rates relative to Base.
        E.g. if Base=USD, returns {'USD': 1.0, 'CAD': 1.35, 'KRW': 1300.0}
        """
        # Logic: always fetch USD based pairs (CAD=X, KRW=X) or USD/CAD, USD/KRW
        # Tickers: 'CAD=X' (USD -> CAD), 'KRW=X' (USD -> KRW)
        now = time.time()
        if self._fx_last_update and (now - self._fx_last_update < self.FX_FRESHNESS_LIMIT):
            return self._fx_cache, False

        rates = {
            "USD": 1.0,
            "CAD": 1.0,  # Fallback
            "KRW": 1.0   # Fallback
        }
        
        try:
            # Fetch USD to CAD
            cad_ticker = yf.Ticker("CAD=X")
            rates["CAD"] = cad_ticker.fast_info.last_price
            
            # Fetch USD to KRW
            krw_ticker = yf.Ticker("KRW=X")
            rates["KRW"] = krw_ticker.fast_info.last_price
            
            self._fx_cache = rates
            self._fx_last_update = now
            return rates, False # False means NOT stale
        except Exception as e:
            print(f"FX Fetch Error: {e}")
            # Return cached if available, else static fallback
            if self._fx_cache:
                return self._fx_cache, True # True means Maybe Stale
            return rates, True # True means Stale/Fallback

