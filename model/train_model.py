import xgboost as xgb
import pandas as pd
import joblib
import os

def train_and_save_model():
    """Carica i dati, addestra un modello XGBoost e lo salva in models/"""

    # Assicuriamoci che la cartella models/ esista
    os.makedirs("models", exist_ok=True)

    # Percorso del file CSV
    data_path = "backtesting/historical_data.csv"

    # Controlla se il file esiste prima di procedere
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Errore: Il file {data_path} non esiste.")

    # Carica i dati
    data = pd.read_csv(data_path)

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

# Esegui il codice solo se lo script è eseguito direttamente
if __name__ == "__main__":
    train_and_save_model()

