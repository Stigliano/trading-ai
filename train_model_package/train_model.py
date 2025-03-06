import xgboost as xgb
import pandas as pd
import joblib
import os
import sys
import subprocess

def train_and_save_model(data_path: str):
    """Carica i dati da data_path (GCS o locale), addestra un modello XGBoost e lo salva in models/"""

    # Assicuriamoci che la cartella models/ esista
    os.makedirs("models", exist_ok=True)

    # Se data_path inizia con 'gs://', scarichiamo il file in locale
    local_csv = "historical_data.csv"
    if data_path.startswith("gs://"):
        print(f"Scarico da GCS: {data_path}")
        # Scarica il file da GCS alla VM
        subprocess.run(["gsutil", "cp", data_path, local_csv], check=True)
    else:
        local_csv = data_path

    if not os.path.exists(local_csv):
        raise FileNotFoundError(f"Errore: Il file {local_csv} non esiste.")

    # Carica i dati
    data = pd.read_csv(local_csv)

    # Controlliamo che le colonne necessarie siano presenti
    required_columns = ["SMA_50", "SMA_200", "RSI", "ATR", "VWAP", "future_return"]
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Colonna mancante nel dataset: {col}")

    # Seleziona le feature e il target
    X = data[["SMA_50", "SMA_200", "RSI", "ATR", "VWAP"]]
    y = data["future_return"]

    # Definizione del modello XGBoost
    model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5)

    print("Inizio addestramento del modello...")
    model.fit(X, y)
    print("Addestramento completato!")

    # Salva il modello
    model_path = "models/xgboost_model.pkl"
    joblib.dump(model, model_path)
    print(f"Modello addestrato e salvato in {model_path}")

import subprocess

# Carica il modello su GCS
bucket_uri = "gs://trading-ai-bucket/xgboost_model.pkl"  # Sostituisci con il tuo percorso preferito
subprocess.run(["gsutil", "cp", model_path, bucket_uri], check=True)
print(f"Modello caricato su GCS: {bucket_uri}")


if __name__ == "__main__":
    # Leggi l'argomento --data_path=...
    data_path = "backtesting/historical_data.csv"
    for arg in sys.argv:
        if arg.startswith("--data_path="):
            data_path = arg.split("=")[1]

    train_and_save_model(data_path)

