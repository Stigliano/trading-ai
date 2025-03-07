import requests
import pandas as pd

def fetch_data(symbol, api_key):
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "compact",
        "datatype": "json"
    }

    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        raise Exception(f"Errore API: {response.status_code}")

    json_data = response.json()
    if "Time Series (Daily)" not in json_data:
        raise Exception(f"Risposta API non valida: {json_data}")

    data = json_data["Time Series (Daily)"]
    df = pd.DataFrame.from_dict(data, orient="index", dtype=float)
    df.index = pd.to_datetime(df.index)
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df = df.sort_index()

    return df

if __name__ == "__main__":
    symbol = "AAPL"
    api_key = "EXLZJSTT9BXDBAJC"  # Inserisci la tua API key qui

    try:
        print(f"📥 Download dati giornalieri per il simbolo {symbol}...")
        data = fetch_data(symbol, api_key)
        print("✅ Dati acquisiti con successo:")
        print(data.head())
        data.to_csv(f"{symbol}_daily.csv")
        print(f"📂 File salvato come: {symbol}_daily.csv")
    except Exception as e:
        print(f"❌ Errore durante acquisizione dati: {e}")

