import os, requests, logging
logger = logging.getLogger(__name__)

FINNHUB_KEY = os.environ.get('FINNHUB_API_KEY', '')

def fetch_stock_quotes(symbols=['AAPL','TSLA','MSFT','AMZN','GOOGL','NVDA','META','BRK.B']):
    if not FINNHUB_KEY: return []
    quotes = []
    for sym in symbols:
        try:
            resp = requests.get(f'https://finnhub.io/api/v1/quote?symbol={sym}&token={FINNHUB_KEY}', timeout=5)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('c', 0) > 0:
                    quotes.append({'symbol': sym, 'price': d['c'], 'change': d.get('dp', 0), 'high': d.get('h', 0), 'low': d.get('l', 0)})
        except Exception:
            pass
    return quotes

def fetch_crypto_quotes():
    """Fetch crypto from CoinGecko (free, no key)."""
    try:
        resp = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,cardano,dogecoin&vs_currencies=usd&include_24hr_change=true', timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            mapping = {'bitcoin':'BTC','ethereum':'ETH','solana':'SOL','binancecoin':'BNB','cardano':'ADA','dogecoin':'DOGE'}
            return [{'symbol': mapping.get(k,k), 'price': v['usd'], 'change': round(v.get('usd_24h_change',0),2)} for k,v in d.items()]
    except Exception:
        pass
    return []

def fetch_commodity_quotes():
    """Fetch commodity prices. Use Yahoo Finance or static with Finnhub."""
    # Finnhub doesn't do commodities easily. Use static but realistic.
    # In production, would use Yahoo Finance or Quandl
    return None  # Return None = panel uses its own data
