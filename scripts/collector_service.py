#!/usr/bin/env python3
"""
Servizio di raccolta dati per trading-ai.
Questo script raccoglie i dati di mercato e li salva.
"""

import os
import sys
import json
import time
import pandas as pd
from flask import Flask, request, jsonify
import logging

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('collector_service')

# Importa modulo fetch_data dalla stessa directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from fetch_data import fetch_data
except ImportError:
    logger.error("Impossibile importare il modulo fetch_data. Assicurati che sia nella stessa directory.")
    sys.exit(1)

# Inizializza Flask
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def collect_data():
    """Endpoint per raccogliere i dati di mercato."""
    if request.method == 'POST':
        try:
            data = request.json
            job_type = data.get('job_type', 'standard')
            
            logger.info(f"Richiesta di raccolta dati ricevuta. Tipo: {job_type}")
            
            # Se è un test, restituisci risposta di successo senza elaborare
            if job_type == 'test':
                return jsonify({"status": "success", "message": "Test completato con successo"})
            
            # Altrimenti, raccogli dati effettivi
            api_key = os.environ.get('ALPHAVANTAGE_API_KEY', 'EXLZJSTT9BXDBAJC')
            symbol = data.get('symbol', 'SPY')  # Default a SPY se non specificato
            
            # Raccogli dati
            market_data = fetch_data(symbol, api_key)
            
            # Elabora e salva dati
            if market_data is not None and not market_data.empty:
                # Calcola indicatori (questo è solo un esempio, adatta alla tua logica)
                market_data['SMA_50'] = market_data['close'].rolling(window=50).mean() / market_data['close']
                market_data['SMA_200'] = market_data['close'].rolling(window=200).mean() / market_data['close']
                market_data['RSI'] = calculate_rsi(market_data['close'])
                market_data['ATR'] = calculate_atr(market_data)
                market_data['VWAP'] = calculate_vwap(market_data)
                
                # Salva i dati elaborati
                output_file = 'collected_data.csv'
                market_data.to_csv(output_file, index=False)
                logger.info(f"Dati salvati in {output_file}")
                
                return jsonify({
                    "status": "success", 
                    "message": f"Dati raccolti per {symbol}",
                    "rows": len(market_data)
                })
            else:
                return jsonify({
                    "status": "warning",
                    "message": "Nessun dato disponibile o mercato chiuso"
                }), 200
                
        except Exception as e:
            logger.error(f"Errore durante la raccolta dati: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        # GET request
        return jsonify({"status": "running", "service": "collector_service"})

def calculate_rsi(prices, window=14):
    """Calcola il Relative Strength Index (RSI)."""
    # Calcolo semplificato, sostituisci con la tua implementazione
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)  # valore default per i primi valori nan

def calculate_atr(data, window=14):
    """Calcola l'Average True Range (ATR)."""
    high = data['high']
    low = data['low']
    close = data['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
    atr = tr.rolling(window=window).mean() / close
    return atr.fillna(0.01)  # valore default

def calculate_vwap(data):
    """Calcola il Volume Weighted Average Price (VWAP)."""
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    vwap = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()
    return vwap

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
