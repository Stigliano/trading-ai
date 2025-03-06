# transformations.py
import pandas as pd
import numpy as np

def compute_indicators(df: pd.DataFrame):
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['SMA_200'] = df['Close'].rolling(200).mean()

    # RSI e ATR potresti calcolarli con TA-Lib o librerie come pandas-ta
    # Esempio di RSI (dummy)
    df['RSI'] = 100 - (100 / (1 + df['Close'].pct_change().add(1).cumprod()))

    return df

def process_data_for_training(df: pd.DataFrame):
    # Pulizia, rimozione righe incomplete, ecc.
    df = df.dropna()
    df = compute_indicators(df)
    # Esempio: future_return su 1 giorno avanti
    df['future_return'] = df['Close'].shift(-1) / df['Close'] - 1
    df = df.dropna(subset=['future_return'])

    return df

