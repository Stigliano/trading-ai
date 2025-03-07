import requests
import pandas as pd
import datetime as dt

# Esempio Binance API per criptovalute (es. Bitcoin)
def get_crypto_data(symbol='BTCUSDT', interval='1h', limit=100):
    url = 'https://api.binance.com/api/v3/klines'
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'n_trades',
        'taker_buy_volume', 'taker_buy_quote_volume', 'ignore'
    ])

    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)

    return df[['open_time', 'open', 'high', 'low', 'close', 'volume']]

# Esempio Alpha Vantage API per azioni (es. Apple AAPL)
ALPHA_VANTAGE_API_KEY = 'EXLZJSTT9BXDBAJC'

def get_stock_data(symbol='AAPL', interval='60min'):
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol,
        'interval': interval,
        'apikey': ALPHA_VANTAGE_API_KEY,
        'outputsize': 'compact'
    }
    response = requests.get(url, params=params)
    data = response.json()

    time_series_key = f'Time Series ({interval})'
    df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
    df.reset_index(inplace=True)
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)

    return df

# Test iniziale immediato
if __name__ == '__main__':
    crypto_df = get_crypto_data()
    stock_df = get_stock_data()

    print('Crypto data (Binance):\n', crypto_df.head())
    print('Stock data (Alpha Vantage):\n', stock_df.head())

