#!/usr/bin/env python3
"""
api_utils.py - Utilities per la gestione delle API finanziarie e il rispetto dei rate limits.
"""

import os
import time
import json
import random
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api_utils')

# Path configurazioni
CONFIG_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / 'config'
API_CONFIG_PATH = CONFIG_DIR / 'api_config.json'

# Crea la directory di configurazione se non esiste
CONFIG_DIR.mkdir(exist_ok=True, parents=True)

# Configurazione predefinita API
DEFAULT_API_CONFIG = {
    "alpha_vantage": {
        "base_url": "https://www.alphavantage.co/query",
        "api_key": os.getenv("ALPHA_VANTAGE_API_KEY", ""),
        "premium": False,
        "rate_limit": {
            "requests_per_minute": 5,
            "requests_per_day": 500,
            "last_request": None,
            "daily_count": 0,
            "daily_reset": None
        }
    },
    "finnhub": {
        "base_url": "https://finnhub.io/api/v1",
        "api_key": os.getenv("FINNHUB_API_KEY", ""),
        "premium": False,
        "rate_limit": {
            "requests_per_minute": 30,
            "requests_per_day": 60,
            "last_request": None,
            "daily_count": 0,
            "daily_reset": None
        }
    },
    "financial_modeling_prep": {
        "base_url": "https://financialmodelingprep.com/api/v3",
        "api_key": os.getenv("FMP_API_KEY", ""),
        "premium": False,
        "rate_limit": {
            "requests_per_minute": 10,
            "requests_per_day": 250,
            "last_request": None,
            "daily_count": 0,
            "daily_reset": None
        }
    },
    "news_api": {
        "base_url": "https://newsapi.org/v2",
        "api_key": os.getenv("NEWS_API_KEY", ""),
        "premium": False,
        "rate_limit": {
            "requests_per_day": 100,
            "last_request": None,
            "daily_count": 0,
            "daily_reset": None
        }
    }
}

def load_api_config():
    """Carica la configurazione delle API."""
    if not API_CONFIG_PATH.exists():
        # Crea file di configurazione predefinito
        with open(API_CONFIG_PATH, 'w') as f:
            json.dump(DEFAULT_API_CONFIG, f, indent=4)
        logger.info(f"✅ Creato file di configurazione API in {API_CONFIG_PATH}")
        return DEFAULT_API_CONFIG
    
    try:
        with open(API_CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        # Aggiungi nuove API se mancanti nel file esistente
        for api, settings in DEFAULT_API_CONFIG.items():
            if api not in config:
                config[api] = settings
                logger.info(f"Aggiunta nuova API: {api}")
        
        # Aggiorna eventuali API key dalle variabili d'ambiente
        for api in config:
            env_key = f"{api.upper().replace('-', '_')}_API_KEY"
            api_key_env = os.getenv(env_key)
            if api_key_env:
                config[api]['api_key'] = api_key_env
        
        return config
    except Exception as e:
        logger.error(f"❌ Errore caricamento configurazione API: {str(e)}")
        return DEFAULT_API_CONFIG

def save_api_config(config):
    """Salva la configurazione delle API."""
    try:
        with open(API_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
        logger.debug("✅ Configurazione API aggiornata")
    except Exception as e:
        logger.error(f"❌ Errore salvataggio configurazione API: {str(e)}")

def check_rate_limit(api_name):
    """
    Verifica se è possibile fare una chiamata API rispettando i rate limits.
    
    Args:
        api_name (str): Nome dell'API da verificare
    
    Returns:
        bool: True se è possibile chiamare l'API, False altrimenti
    """
    config = load_api_config()
    
    if api_name not in config:
        logger.error(f"❌ API {api_name} non configurata")
        return False
    
    api_config = config[api_name]
    rate_limit = api_config['rate_limit']
    now = datetime.now()
    
    # Inizializza o resetta contatore giornaliero
    if not rate_limit.get('daily_reset') or datetime.fromisoformat(rate_limit['daily_reset']) < now:
        rate_limit['daily_count'] = 0
        rate_limit['daily_reset'] = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()
    
    # Verifica limite giornaliero
    if rate_limit['daily_count'] >= rate_limit['requests_per_day']:
        logger.warning(f"⚠️ Limite giornaliero superato per {api_name}")
        return False
    
    # Verifica limite al minuto
    if 'requests_per_minute' in rate_limit:
        if rate_limit.get('last_request'):
            last_request_time = datetime.fromisoformat(rate_limit['last_request'])
            seconds_since_last = (now - last_request_time).total_seconds()
            
            # Calcola ritardo necessario
            seconds_per_request = 60 / rate_limit['requests_per_minute']
            if seconds_since_last < seconds_per_request:
                wait_time = seconds_per_request - seconds_since_last
                logger.info(f"⏳ Attesa {wait_time:.2f} secondi per rispettare il rate limit di {api_name}")
                time.sleep(wait_time)
    
    return True

def update_rate_limit(api_name):
    """
    Aggiorna i contatori rate limit dopo una chiamata API.
    
    Args:
        api_name (str): Nome dell'API da aggiornare
    """
    config = load_api_config()
    
    if api_name in config:
        rate_limit = config[api_name]['rate_limit']
        rate_limit['last_request'] = datetime.now().isoformat()
        rate_limit['daily_count'] += 1
        save_api_config(config)

def get_api_key(api_name):
    """
    Ottiene la API key per il servizio specificato.
    
    Args:
        api_name (str): Nome dell'API
    
    Returns:
        str: API key o stringa vuota se non configurata
    """
    config = load_api_config()
    
    if api_name in config:
        return config[api_name]['api_key']
    
    return ""

def get_base_url(api_name):
    """
    Ottiene l'URL base per il servizio API specificato.
    
    Args:
        api_name (str): Nome dell'API
    
    Returns:
        str: URL base o None se non configurato
    """
    config = load_api_config()
    
    if api_name in config:
        return config[api_name]['base_url']
    
    return None

def make_api_request(api_name, endpoint="", params=None, method="GET", retries=3, 
                     retry_wait=5, rotate_vpn=False):
    """
    Effettua una richiesta API rispettando i rate limits.
    
    Args:
        api_name (str): Nome dell'API
        endpoint (str): Endpoint specifico da chiamare
        params (dict): Parametri della richiesta
        method (str): Metodo HTTP (GET, POST, etc.)
        retries (int): Numero di tentativi in caso di errore
        retry_wait (int): Secondi di attesa tra i tentativi
        rotate_vpn (bool): Se True, tenta rotazione VPN in caso di errori
    
    Returns:
        dict: Risposta JSON o None in caso di errore
    """
    config = load_api_config()
    
    if api_name not in config:
        logger.error(f"❌ API {api_name} non configurata")
        return None
    
    api_config = config[api_name]
    base_url = api_config['base_url']
    api_key = api_config['api_key']
    
    if not api_key:
        logger.error(f"❌ API key per {api_name} non configurata")
        return None
    
    # Prepara l'URL
    url = f"{base_url}/{endpoint}".rstrip('/')
    
    # Prepara i parametri
    if params is None:
        params = {}
    
    # Aggiungi API key ai parametri (se non è già inclusa)
    if api_name == "alpha_vantage" and 'apikey' not in params:
        params['apikey'] = api_key
    elif api_name == "finnhub":
        # Finnhub usa header per API key
        headers = {"X-Finnhub-Token": api_key}
    elif api_name == "financial_modeling_prep" and 'apikey' not in params:
        params['apikey'] = api_key
    elif api_name == "news_api" and 'apiKey' not in params:
        params['apiKey'] = api_key
    else:
        # Opzione generica per altre API
        headers = {"Authorization": f"Bearer {api_key}"}
    
    # Flag per retry
    should_retry = False
    attempts = 0
    
    while attempts < retries:
        attempts += 1
        
        try:
            # Verifica rate limit
            if not check_rate_limit(api_name):
                logger.warning(f"⚠️ Rate limit per {api_name} superato, attesa...")
                time.sleep(retry_wait * 2)  # Attesa doppia se rate limit superato
                continue
            
            # Effettua la richiesta
            if method.upper() == "GET":
                if api_name == "finnhub":
                    response = requests.get(url, params=params, headers=headers)
                elif "headers" in locals():
                    response = requests.get(url, params=params, headers=headers)
                else:
                    response = requests.get(url, params=params)
            elif method.upper() == "POST":
                if api_name == "finnhub":
                    response = requests.post(url, json=params, headers=headers)
                elif "headers" in locals():
                    response = requests.post(url, json=params, headers=headers)
                else:
                    response = requests.post(url, json=params)
            else:
                logger.error(f"❌ Metodo {method} non supportato")
                return None
            
            # Aggiorna contatori rate limit
            update_rate_limit(api_name)
            
            # Verifica risposta
            if response.status_code == 200:
                # Successo
                try:
                    return response.json()
                except ValueError:
                    # Alcune API potrebbero non tornare JSON
                    return {"status": "success", "text": response.text}
            
            # Gestione errori
            if response.status_code == 429:  # Too Many Requests
                logger.warning(f"⚠️ Rate limit superato per {api_name} (429)")
                should_retry = True
                retry_wait = retry_wait * 2  # Backoff esponenziale
                
                # Se opzione abilitata, tenta rotazione VPN
                if rotate_vpn:
                    try:
                        # Import condizionale per evitare dipendenze circolari
                        from scripts.utils.vpn_utils import rotate_vpn_if_needed
                        rotate_vpn_if_needed()
                    except ImportError:
                        logger.warning("⚠️ Modulo vpn_utils non disponibile")
            
            elif response.status_code >= 500:  # Errori server
                logger.warning(f"⚠️ Errore server per {api_name}: {response.status_code}")
                should_retry = True
            else:
                logger.error(f"❌ Errore API {api_name}: {response.status_code} - {response.text}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Errore richiesta a {api_name}: {str(e)}")
            should_retry = True
        
        # Gestione retry
        if should_retry and attempts < retries:
            wait_time = retry_wait * attempts  # Backoff lineare
            logger.info(f"⏳ Attesa {wait_time}s prima del tentativo {attempts+1}/{retries}")
            time.sleep(wait_time)
        else:
            break
    
    return None

def register_api_key(api_name, api_key, premium=False):
    """
    Registra una nuova API key nella configurazione.
    
    Args:
        api_name (str): Nome dell'API
        api_key (str): Chiave API da registrare
        premium (bool): Se l'account è premium
    
    Returns:
        bool: True se registrata con successo, False altrimenti
    """
    config = load_api_config()
    
    if api_name in config:
        config[api_name]['api_key'] = api_key
        config[api_name]['premium'] = premium
        
        # Aggiorna rate limits in base al piano premium
        if premium:
            if api_name == "alpha_vantage":
                config[api_name]['rate_limit']['requests_per_minute'] = 75
                config[api_name]['rate_limit']['requests_per_day'] = 5000
            elif api_name == "finnhub":
                config[api_name]['rate_limit']['requests_per_minute'] = 60
                config[api_name]['rate_limit']['requests_per_day'] = 800
            elif api_name == "financial_modeling_prep":
                config[api_name]['rate_limit']['requests_per_minute'] = 30
                config[api_name]['rate_limit']['requests_per_day'] = 1000
        
        save_api_config(config)
        logger.info(f"✅ API key per {api_name} registrata con successo")
        return True
    else:
        logger.error(f"❌ API {api_name} non supportata")
        return False

def test_api_key(api_name):
    """
    Testa una API key per verificare se è valida.
    
    Args:
        api_name (str): Nome dell'API da testare
    
    Returns:
        bool: True se l'API key è valida, False altrimenti
    """
    if api_name == "alpha_vantage":
        # Test Alpha Vantage
