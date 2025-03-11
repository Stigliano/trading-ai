#!/usr/bin/env python3
"""
Servizio API per trading-ai.
Questo script espone un endpoint per fare previsioni utilizzando il modello addestrato.
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np
import joblib
from flask import Flask, request, jsonify
import logging
from google.cloud import storage

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api_service')

# Inizializza Flask
app = Flask(__name__)

# Carica il modello
MODEL_PATH = os.environ.get('MODEL_PATH', 'models/xgboost_model.pkl')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'trading-ai-bucket')
RUN_LOCAL = os.environ.get('RUN_LOCAL', 'true').lower() == 'true'

def load_model():
    """Carica il modello XGBoost."""
    model = None
    
    # Prova prima localmente
    local_paths = [
        MODEL_PATH,
        "models/xgboost_model.pkl",
        "xgboost_model_artifact/xgboost_model.pkl"
    ]
    
    for path in local_paths:
        if os.path.exists(path):
            logger.info(f"Caricamento modello da {path}")
            model = joblib.load(path)
            break
    
    # Se non trovato localmente e non siamo in modalità locale, prova da GCS
    if model is None and not RUN_LOCAL:
        try:
            logger.info(f"Tentativo di caricamento modello da GCS bucket: {BUCKET_NAME}")
            storage_client = storage.Client()
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob("xgboost_model.pkl")
            
            # Scarica in un file temporaneo
            temp_path = "/tmp/temp_model.pkl"
            blob.download_to_filename(temp_path)
            
            model = joblib.load(temp_path)
            logger.info("Modello caricato con successo da GCS")
        except Exception as e:
            logger.error(f"Errore durante il caricamento del modello da GCS: {str(e)}")
    
    if model is None:
        logger.error("Impossibile caricare il modello da nessuna fonte")
        raise FileNotFoundError("Modello non trovato")
        
    return model

# Carica il modello all'avvio
try:
    model = load_model()
except Exception as e:
    logger.error(f"Errore durante il caricamento del modello: {str(e)}")
    model = None

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint per verificare lo stato dell'API."""
    if model is not None:
        return jsonify({"status": "healthy", "message": "API pronta per l'uso"})
    else:
        return jsonify({"status": "degraded", "message": "Modello non caricato"}), 503

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint per generare previsioni."""
    if model is None:
        return jsonify({
            "status": "error",
            "message": "Modello non disponibile"
        }), 503
    
    try:
        # Ottieni i dati dalla richiesta
        data = request.json
        
        # Controllo formato: singolo record o più record
        if isinstance(data, dict):
            # Singolo record
            required_features = ["SMA_50", "SMA_200", "RSI", "ATR", "VWAP"]
            for feature in required_features:
                if feature not in data:
                    return jsonify({
                        "status": "error",
                        "message": f"Feature richiesta mancante: {feature}"
                    }), 400
            
            # Crea DataFrame da un singolo record
            input_data = pd.DataFrame([data])
        else:
            # Lista di record
            input_data = pd.DataFrame(data)
        
        # Effettua la previsione
        predictions = model.predict(input_data)
        
        # Genera decisioni di trading basate sulle previsioni
        decisions = []
        for pred in predictions:
            if pred > 0.02:
                decision = "BUY"
            elif pred < -0.01:
                decision = "SELL"
            else:
                decision = "HOLD"
            decisions.append(decision)
        
        # Prepara la risposta
        if len(predictions) == 1:
            # Singolo record
            response = {
                "status": "success",
                "market_prediction": float(predictions[0]),
                "trading_decision": decisions[0]
            }
        else:
            # Più record
            response = {
                "status": "success",
                "market_predictions": predictions.tolist(),
                "trading_decisions": decisions
            }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Errore durante la generazione della previsione: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
