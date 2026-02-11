import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class AnalyticsEngine:
    """
    Handles complex calculations: Sharpe Ratio, Portfolio Returns, and Risk Analysis.
    """
    def __init__(self, risk_free_rate=0.045):
        self.risk_free_rate = risk_free_rate # Annualized 4.5%

    def fetch_historical_data(self, assets, period="1y"):
        """
        Fetches historical prices (Close) for all assets.
        Returns a DataFrame of prices with Tickers as columns.
        """
        if not assets:
            return pd.DataFrame()
        
        tickers = [a['ticker'] for a in assets]
        try:
            # Batch fetch
            data = yf.download(tickers, period=period, progress=False)
            
            # Handle Data Structure (yfinance varies by version)
            prices = pd.DataFrame()
            
            # Case 1: MultiIndex columns (PriceType, Ticker) or (Ticker, PriceType)
            if isinstance(data.columns, pd.MultiIndex):
                # Try getting Adj Close first from level 0 or 1
                try:
                    prices = data['Adj Close']
                except KeyError:
                    try:
                        # Sometimes it's (Ticker, 'Adj Close')
                        if 'Adj Close' in data.columns.get_level_values(1):
                             prices = data.xs('Adj Close', axis=1, level=1)
                        else:
                             prices = data['Close']
                    except KeyError:
                        return pd.DataFrame()
            # Case 2: Single Level Columns
            else:
                # If only one ticker, it might be just columns like [Open, Close, ...]
                if len(tickers) == 1:
                    if 'Adj Close' in data:
                        prices = data[['Adj Close']].copy()
                        prices.columns = tickers
                    elif 'Close' in data:
                        prices = data[['Close']].copy()
                        prices.columns = tickers
                else:
                    # Flat structure?
                    if 'Adj Close' in data:
                         prices = data['Adj Close']
                    elif 'Close' in data:
                         prices = data['Close']

            # Ensure all tickers are present
            # Filter out tickers that failed to download or are missing
            valid_prices = pd.DataFrame()
            for t in tickers:
                if t in prices.columns:
                    valid_prices[t] = prices[t]
            
            return valid_prices
        except Exception as e:
            print(f"Error fetching history: {e}")
            return pd.DataFrame()

    def calculate_sharpe_ratio(self, assets, ex_btc=False):
        """
        Calculates the Sharpe Ratio of the portfolio.
        Optionally excludes Bitcoin (or Crypto) from the calculation.
        """
        # Filter assets if Ex-BTC is requested
        active_assets = assets
        if ex_btc:
            active_assets = [a for a in assets if "BTC" not in a['ticker'] and a['asset_class'] != 'Crypto']
            
        if not active_assets:
            return 0.0, 0.0, pd.Series()

        # Fetch History
        prices = self.fetch_historical_data(active_assets)
        if prices.empty:
            return 0.0, 0.0, pd.Series()

        # Forward fill to handle mismatches or holidays
        prices = prices.ffill().dropna()

        if prices.empty:
            return 0.0, 0.0, pd.Series()
        
        # Calculate Weighted Portfolio Value History
        portfolio_value_series = pd.Series(0.0, index=prices.index)
        
        valid_assets_count = 0
        for asset in active_assets:
            ticker = asset['ticker']
            if ticker in prices.columns:
                qty = asset['quantity']
                # Add asset value to portfolio total
                asset_val = prices[ticker] * qty
                portfolio_value_series = portfolio_value_series.add(asset_val, fill_value=0)
                valid_assets_count += 1
        
        if valid_assets_count == 0:
             return 0.0, 0.0, pd.Series()

        # Determine start of portfolio (first non-zero value)
        portfolio_value_series = portfolio_value_series[portfolio_value_series > 0]
        
        if portfolio_value_series.empty or len(portfolio_value_series) < 5:
            return 0.0, 0.0, pd.Series()

        # Calculate Returns
        portfolio_returns = portfolio_value_series.pct_change().dropna()
        
        if portfolio_returns.empty:
            return 0.0, 0.0, portfolio_value_series

        mean_daily_return = portfolio_returns.mean()
        std_daily_return = portfolio_returns.std()
        
        if std_daily_return == 0:
            return 0.0, 0.0, portfolio_value_series

        rf_daily = (1 + self.risk_free_rate) ** (1/252) - 1
        
        # Annualized Sharpe
        sharpe_ratio = (mean_daily_return - rf_daily) / std_daily_return * np.sqrt(252)
        annual_volatility = std_daily_return * np.sqrt(252)
        
        return sharpe_ratio, annual_volatility, portfolio_value_series

    def calculate_manual_sharpe(self, annual_roi, annual_vol, risk_free_rate):
        """
        Calculates Sharpe Ratio from manual inputs.
        Annual ROI and Volatility should be decimals (e.g., 0.20 for 20%).
        """
        if annual_vol == 0:
            return 0.0
        return (annual_roi - risk_free_rate) / annual_vol

    def get_portfolio_news(self, assets, limit_per_asset=3):
        """Fetches news for ALL assets in the portfolio."""
        if not assets:
            return []
            
        tickers = [a['ticker'] for a in assets if a['ticker'] != 'CASH']
        news_items = []
        
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                raw_news = t.news
                if raw_news:
                    count = 0
                    for item in raw_news:
                        if count >= limit_per_asset: break
                        try:
                            if not isinstance(item, dict): continue
                            content = item.get('content', item)
                            if not isinstance(content, dict): content = {}

                            parsed = {
                                'ticker': ticker,
                                'title': content.get('title', 'No Title'),
                                'link': content.get('clickThroughUrl', {}).get('url') if isinstance(content.get('clickThroughUrl'), dict) else content.get('clickThroughUrl'),
                                'providerPublishTime': content.get('pubDate') or item.get('providerPublishTime')
                            }
                            if not any(n['link'] == parsed['link'] for n in news_items):
                                news_items.append(parsed)
                                count += 1
                        except Exception:
                            continue
            except Exception:
                continue
                
        return news_items
