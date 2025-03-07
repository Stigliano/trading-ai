import requests
import pandas as pd
import os
from db_utils import get_engine, save_dataframe_to_db
from dotenv import load_dotenv

load_dotenv()

def fetch_data_intraday(symbol, api_key, interval="60min"):
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": interval,
        "apikey": api_key
    }

    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        raise Exception(f"Errore API: {response.status_code}")

    json_data = response.json()
    time_series_key = f"Time Series ({interval})"
    if time_series_key not in json_data:
        raise Exception(f"Risposta API non valida: {json_data}")

    data = json_data[time_series_key]
    df = pd.DataFrame.from_dict(data, orient="index")
    df.index = pd.to_datetime(df.index)
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df.sort_index(inplace=True)

    return df

if __name__ == "__main__":
    symbol = "AAPL"
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    df = fetch_data_intraday(symbol, api_key)
    engine = get_engine()
    save_dataframe_to_db(df, "intraday_data", engine)

    print("✅ Dati intraday salvati nel database.")

