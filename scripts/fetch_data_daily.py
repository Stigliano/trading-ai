import requests
import pandas as pd
from db_utils import get_db_engine, save_dataframe_to_db
import os
from dotenv import load_dotenv

load_dotenv()

def fetch_data_daily(symbol, api_key):
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()

    data = response.json().get("Time Series (Daily)")
    if not data:
        raise ValueError("❌ Risposta API invalida o dati mancanti!")

    df = pd.DataFrame.from_dict(data, orient="index", dtype=float)
    df.index = pd.to_datetime(df.index)
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df.sort_index(inplace=True)
    return df

if __name__ == "__main__":
    symbol = "AAPL"
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    engine = get_db_engine()
    df = fetch_data_daily(symbol, api_key)

    save_dataframe_to_db(df, "stock_daily_prices", engine)
    print(f"✅ Dati giornalieri {symbol} acquisiti e salvati nel database!")

