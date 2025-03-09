import os
import joblib
from fastapi import FastAPI

# Percorso del modello
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "xgboost_model.pkl")

app = FastAPI()

# Verifica che il modello esista prima di caricarlo
if os.path.exists(MODEL_PATH):
    xgb_model = joblib.load(MODEL_PATH)
    print("✅ Modello caricato con successo!")
else:
    raise FileNotFoundError(f"❌ Errore: Il file '{MODEL_PATH}' non è stato trovato.")

@app.get("/")
async def root():
    return {"message": "Trading AI API is running!"}
