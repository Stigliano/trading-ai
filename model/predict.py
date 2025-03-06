import joblib
import pandas as pd

# Carica il modello
model = joblib.load("models/xgboost_model.pkl")

# Simula nuovi dati di input
new_data = pd.DataFrame([[1.2, 0.8, 50, 1.5, 100]], columns=["SMA_50", "SMA_200", "RSI", "ATR", "VWAP"])

# Effettua la previsione
prediction = model.predict(new_data)

print(f"Previsione: {prediction}")
