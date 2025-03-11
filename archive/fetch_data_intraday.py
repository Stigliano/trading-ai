#!/usr/bin/env python3
"""
Script per scaricare dati intraday (ogni ora) da Alpha Vantage.
Ottimizzato per gestire limiti di rate-limiting e salvataggio su PostgreSQL.
"""

import os
import sys
import time
import logging
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Aggiungiamo il percorso della directory principale
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.db_utils import get_db_engine, save_dataframe_to_db
except ImportError:
    print("❌ Importazione moduli fallita. Assicurati di essere nella directory corretta.")
    sys.exit(1)

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/fetch_data_intraday.log", mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fetch_data_intraday')

# Crea directory per i log se non esiste
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Carica variabili d'ambiente
load_dotenv()
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY') or os.getenv('ALPHAVANTAGE_API_KEY')
SYMBOLS = os.getenv('SYMBOLS', 'SPY,QQQ,AAPL,MSFT,GOOGL').split(',')
INTERVAL = os.getenv('INTRADAY_INTERVAL', '60min')

def fetch_data_intraday(symbol, api_key, interval=INTERVAL, output_size="compact"):
    """
    Scarica i dati intraday per un simbolo specifico da Alpha Vantage.
    
    Args:
        symbol (str): Simbolo dell'azione (es. "AAPL")
        api_key (str): API key Alpha Vantage
        interval (str): Intervallo di tempo (default: variabile d'ambiente o "60min")
        output_size (str): "compact" o "full" (default: "compact")
        
    Returns:
        pandas.DataFrame: DataFrame con i dati
    """
    try:
        logger.info(f"Scaricamento dati intraday per {symbol} con intervallo {interval}...")
        
        # URL dell'API
        base_url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "outputsize": output_size,
            "apikey": api_key
        }
        
        # Effettua la richiesta
        response = requests.get(base_url, params=params)
        
        # Verifica se ci sono errori HTTP
        if response.status_code != 200:
            logger.error(f"Errore HTTP {response.status_code}: {response.text}")
            return None
        
        data = response.json()
        
        # Controlla se ci sono errori nella risposta
        if "Error Message" in data:
            logger.error(f"Errore nell'API: {data['Error Message']}")
            return None
            
        # Verifica la presenza di messaggi relativi a rate limit
        if "Note" in data and "API call frequency" in data["Note"]:
            logger.warning(f"Rate limit raggiunto: {data['Note']}")
            logger.info("Attesa di 60 secondi prima del prossimo tentativo...")
            time.sleep(60)
            return fetch_data_intraday(symbol, api_key, interval, output_size)
        
        # Chiave corretta per i dati intraday
        time_series_key = f"Time Series ({interval})"
        if time_series_key not in data:
            logger.error(f"Dati intraday non trovati nella risposta API. Chiavi disponibili: {list(data.keys())}")
            return None
            
        # Estrai i dati della serie temporale
        time_series = data[time_series_key]
        
        # Converti in DataFrame
        df = pd.DataFrame.from_dict(time_series, orient="index", dtype=float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # Rinomina colonne - gestisce sia il formato con prefisso che senza
        if all(col.startswith(('1. ', '2. ', '3. ', '4. ', '5. ')) for col in df.columns):
            df.columns = [c.split('. ')[1] for c in df.columns]
        else:
            # Assicurati che ci siano le colonne standardizzate
            standard_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in standard_columns):
                logger.warning("Formato colonne non standard. Rinomino in base alla posizione.")
                if len(df.columns) >= 5:
                    df.columns = standard_columns[:len(df.columns)]
                else:
                    logger.error(f"Insufficienti colonne nei dati: {df.columns}")
                    return None
        
        # Aggiungi colonne aggiuntive
        df['symbol'] = symbol
        df['interval'] = interval
            
        logger.info(f"✅ Scaricati {len(df)} record intraday per {symbol}")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Errore durante il download dei dati intraday per {symbol}: {str(e)}")
        return None

def process_all_symbols():
    """Elabora tutti i simboli definiti nelle variabili d'ambiente."""
    logger.info(f"Inizio elaborazione dati intraday per {len(SYMBOLS)} simboli con intervallo {INTERVAL}")
    
    # Cerca di stabilire una connessione al database
    try:
        engine = get_db_engine()
        db_available = True
        logger.info("✅ Connessione al database stabilita")
    except Exception as e:
        logger.warning(f"⚠️ Database non disponibile: {str(e)}")
        logger.warning("⚠️ I dati saranno salvati solo localmente")
        db_available = False
        engine = None
    
    for i, symbol in enumerate(SYMBOLS):
        try:
            # Scarica dati
            df = fetch_data_intraday(symbol, API_KEY, INTERVAL)
            
            if df is not None and not df.empty:
                # Salva nel database se disponibile
                if db_available:
                    success = save_dataframe_to_db(df, "intraday_data", engine)
                    if success:
                        logger.info(f"✅ Dati intraday per {symbol} salvati nel database")
                    else:
                        logger.error(f"❌ Errore durante il salvataggio dei dati intraday per {symbol} nel database")
                
                # Salva sempre in file CSV come backup
                output_file = f"data/{symbol}_intraday_{INTERVAL}.csv"
                df.to_csv(output_file)
                logger.info(f"✅ Dati intraday per {symbol} salvati in {output_file}")
                    
            # Pausa tra le richieste per rispettare i limiti di API
            if i < len(SYMBOLS) - 1:
                pause_time = 15  # Alpha Vantage consiglia una pausa di 12+ secondi
                logger.info(f"Pausa di {pause_time} secondi prima del prossimo simbolo...")
                time.sleep(pause_time)
        
        except Exception as e:
            logger.error(f"❌ Errore nell'elaborazione di {symbol}: {str(e)}")

if __name__ == "__main__":
    logger.info("🚀 Avvio script fetch_data_intraday.py")
    
    if not API_KEY:
        logger.error("❌ API key di Alpha Vantage non configurata!")
        sys.exit(1)
    
    # Elabora tutti i simboli
    process_all_symbols()
    
    logger.info("✅ Elaborazione dati intraday completata")
