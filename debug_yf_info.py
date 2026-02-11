import yfinance as yf
import json

tickers = ['SPY', 'QQQ', 'GLD', 'NVDA', 'BTC-USD']

print("-" * 50)
for t in tickers:
    print(f"FETCHING {t}...")
    try:
        tick = yf.Ticker(t)
        info = tick.info
        
        # Extract key fields for debugging
        debug_data = {
            'quoteType': info.get('quoteType'),
            'sector': info.get('sector'),
            'category': info.get('category'),
            'assetProfile': info.get('assetProfile'), # Sometimes hidden here?
            'legalType': info.get('legalType'),
            'shortName': info.get('shortName')
        }
        
        print(f"DATA FOR {t}:")
        print(json.dumps(debug_data, indent=2))
    except Exception as e:
        print(f"ERROR {t}: {e}")
    print("-" * 50)
