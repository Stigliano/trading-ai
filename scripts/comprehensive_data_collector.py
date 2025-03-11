#!/usr/bin/env python3
"""
comprehensive_data_collector.py - Script per raccogliere dati finanziari completi da fonti gratuite.
Utilizza l'infrastruttura esistente ma espande i tipi di dati raccolti.
"""

import os
import sys
import time
import logging
import pandas as pd
import requests
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Aggiunge il percorso principale del progetto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.db_utils import get_db_engine, save_dataframe_to_db
except ImportError:
    print("❌ Moduli db_utils non trovati. Assicurati di essere nella directory corretta.")
    sys.exit(1)

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/comprehensive_data.log", mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('comprehensive_data')

# Crea directory per i log e dati se non esistono
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Carica variabili d'ambiente
load_dotenv()
SYMBOLS = os.getenv('SYMBOLS', 'SPY,QQQ,AAPL,MSFT,GOOGL').split(',')
FRED_API_KEY = os.getenv('FRED_API_KEY', '')  # Opzionale, registrabile gratuitamente

# User agent per scraping
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
]

def get_market_data_from_yahoo(symbol, period="2y", interval="1d"):
    """Ottiene dati di mercato da Yahoo Finance."""
    try:
        logger.info(f"Raccolta dati di mercato Yahoo Finance per {symbol}")
        
        # Verifica se yfinance è installato
        try:
            import yfinance as yf
        except ImportError:
            logger.error("yfinance non installato. Installare con: pip install yfinance")
            return None
            
        data = yf.download(symbol, period=period, interval=interval, progress=False)
        
        if data.empty:
            logger.warning(f"Nessun dato trovato per {symbol}")
            return None
            
        # Aggiungi metadata
        data['symbol'] = symbol
        data['source'] = 'yahoo_finance'
        
        logger.info(f"✅ Raccolti {len(data)} record per {symbol}")
        return data
        
    except Exception as e:
        logger.error(f"❌ Errore durante la raccolta dati Yahoo Finance per {symbol}: {str(e)}")
        return None

def get_fundamental_data(symbol):
    """Ottiene dati fondamentali da Yahoo Finance."""
    try:
        logger.info(f"Raccolta dati fondamentali per {symbol}")
        
        # Verifica se yfinance è installato
        try:
            import yfinance as yf
        except ImportError:
            logger.error("yfinance non installato. Installare con: pip install yfinance")
            return {}
            
        ticker = yf.Ticker(symbol)
        
        # Raccoglie diversi tipi di dati fondamentali
        fundamentals = {}
        
        # Info di base
        info = ticker.info
        if info:
            fundamentals['info'] = pd.DataFrame([info])
        
        # Bilanci
        financials = ticker.financials
        if not isinstance(financials, type(None)) and not financials.empty:
            fundamentals['financials'] = financials.T.reset_index()
            fundamentals['financials']['symbol'] = symbol
        
        # Stato patrimoniale
        balance = ticker.balance_sheet
        if not isinstance(balance, type(None)) and not balance.empty:
            fundamentals['balance'] = balance.T.reset_index()
            fundamentals['balance']['symbol'] = symbol
        
        # Flussi di cassa
        cashflow = ticker.cashflow
        if not isinstance(cashflow, type(None)) and not cashflow.empty:
            fundamentals['cashflow'] = cashflow.T.reset_index()
            fundamentals['cashflow']['symbol'] = symbol
        
        # Stime degli analisti
        earnings = ticker.earnings
        if not isinstance(earnings, type(None)):
            if isinstance(earnings, pd.DataFrame) and not earnings.empty:
                fundamentals['earnings'] = earnings.reset_index()
                fundamentals['earnings']['symbol'] = symbol
            elif isinstance(earnings, dict):
                fundamentals['earnings'] = pd.DataFrame([earnings])
                fundamentals['earnings']['symbol'] = symbol
        
        logger.info(f"✅ Raccolti dati fondamentali per {symbol} ({len(fundamentals)} set)")
        return fundamentals
        
    except Exception as e:
        logger.error(f"❌ Errore durante la raccolta dati fondamentali per {symbol}: {str(e)}")
        return {}

def get_news_sentiment(symbol, limit=10):
    """
    Raccoglie notizie e analisi del sentiment da fonti gratuite.
    Questa è una componente dell'analisi qualitativa.
    """
    try:
        logger.info(f"Raccolta news e sentiment per {symbol}")
        
        # Yahoo Finance - Ultime notizie
        headers = {
            'User-Agent': random.choice(USER_AGENTS)
        }
        
        url = f"https://finance.yahoo.com/quote/{symbol}/news"
        response = requests.get(url, headers=headers)
        
        # Semplice estrazione di notizie (analisi basilare)
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_items = []
            # Estrazione basica delle notizie (adatta in base alla struttura HTML)
            articles = soup.select('div.Ov\(h\) Pend\(44px\)') or soup.select('h3.Mb\(5px\)')
            
            for article in articles[:limit]:
                try:
                    title = article.get_text().strip()
                    news_items.append({
                        'title': title,
                        'symbol': symbol,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                    })
                except:
                    pass
            
            if news_items:
                news_df = pd.DataFrame(news_items)
                logger.info(f"✅ Raccolte {len(news_df)} notizie per {symbol}")
                return news_df
        
        logger.warning(f"Nessuna notizia trovata per {symbol} o format HTML cambiato")
        return None
    
    except Exception as e:
        logger.error(f"❌ Errore durante la raccolta news per {symbol}: {str(e)}")
        return None

def get_macroeconomic_data():
    """Ottiene dati macroeconomici da FRED API."""
    if not FRED_API_KEY:
        logger.warning("⚠️ FRED API KEY non configurata. Dati macroeconomici non disponibili.")
        return {}
        
    try:
        try:
            from fredapi import Fred
        except ImportError:
            logger.error("fredapi non installato. Installare con: pip install fredapi")
            return {}
            
        fred = Fred(api_key=FRED_API_KEY)
        
        # Indicatori chiave da raccogliere
        indicators = {
            'GDP': 'Gross Domestic Product',
            'UNRATE': 'Unemployment Rate',
            'CPIAUCSL': 'Consumer Price Index',
            'FEDFUNDS': 'Federal Funds Rate',
            'T10Y2Y': 'Treasury Yield Spread',
            'DEXUSEU': 'USD/EUR Exchange Rate',
            'VIXCLS': 'VIX Volatility Index',
            'SP500': 'S&P 500 Index'
        }
        
        macro_data = {}
        for series_id, name in indicators.items():
            try:
                df = fred.get_series(series_id, observation_start=(datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d'))
                if len(df) > 0:
                    df = df.reset_index()
                    df.columns = ['date', 'value']
                    df['indicator'] = series_id
                    df['name'] = name
                    macro_data[series_id] = df
                    logger.info(f"✅ Raccolti {len(df)} record per {name}")
                    time.sleep(0.5)  # Rispetta rate limit
            except Exception as e:
                logger.error(f"❌ Errore per indicatore {series_id}: {str(e)}")
        
        return macro_data
                
    except Exception as e:
        logger.error(f"❌ Errore durante la raccolta dati macroeconomici: {str(e)}")
        return {}

def get_options_data(symbol):
    """Ottiene dati sulle opzioni da Yahoo Finance."""
    try:
        logger.info(f"Raccolta dati opzioni per {symbol}")
        
        # Verifica se yfinance è installato
        try:
            import yfinance as yf
        except ImportError:
            logger.error("yfinance non installato. Installare con: pip install yfinance")
            return None
            
        ticker = yf.Ticker(symbol)
        
        # Ottieni le date di scadenza disponibili
        expirations = ticker.options
        
        if not expirations or len(expirations) == 0:
            logger.warning(f"Nessuna data di scadenza opzioni trovata per {symbol}")
            return None
            
        # Prendi solo le prime 3 scadenze per non sovraccaricare
        expiry_dates = expirations[:3]
        
        all_options = []
        for expiry in expiry_dates:
            # Ottieni calls e puts
            option_chain = ticker.option_chain(expiry)
            calls = option_chain.calls
            puts = option_chain.puts
            
            if not calls.empty:
                calls['option_type'] = 'call'
                calls['expiry'] = expiry
                calls['symbol'] = symbol
                all_options.append(calls)
                
            if not puts.empty:
                puts['option_type'] = 'put'
                puts['expiry'] = expiry
                puts['symbol'] = symbol
                all_options.append(puts)
                
            time.sleep(1)  # Previeni rate limiting
        
        if all_options:
            options_df = pd.concat(all_options, ignore_index=True)
            logger.info(f"✅ Raccolti {len(options_df)} contratti di opzione per {symbol}")
            return options_df
        else:
            return None
            
    except Exception as e:
        logger.error(f"❌ Errore durante la raccolta dati opzioni per {symbol}: {str(e)}")
        return None

def get_sector_performance():
    """Ottiene dati sulle performance dei settori per analisi qualitativa."""
    try:
        logger.info("Raccolta dati performance settoriali...")
        
        # Verifica se yfinance è installato
        try:
            import yfinance as yf
        except ImportError:
            logger.error("yfinance non installato. Installare con: pip install yfinance")
            return None
        
        # ETF che rappresentano diversi settori
        sector_etfs = {
            'XLF': 'Financial',
            'XLK': 'Technology',
            'XLE': 'Energy',
            'XLV': 'Healthcare',
            'XLI': 'Industrial',
            'XLP': 'Consumer Staples',
            'XLY': 'Consumer Discretionary',
            'XLB': 'Materials',
            'XLU': 'Utilities',
            'XLRE': 'Real Estate'
        }
        
        # Ottieni i dati di performance
        performance_data = []
        for etf, sector in sector_etfs.items():
            try:
                data = yf.download(etf, period="1mo", interval="1d", progress=False)
                if not data.empty:
                    # Calcola la performance
                    first_close = data['Close'].iloc[0]
                    last_close = data['Close'].iloc[-1]
                    perf_1mo = ((last_close / first_close) - 1) * 100
                    
                    # Aggiungi alla lista
                    performance_data.append({
                        'sector': sector,
                        'etf': etf,
                        'performance_1mo': perf_1mo,
                        'last_price': last_close,
                        'date': data.index[-1]
                    })
                    
                    time.sleep(0.5)  # Previeni rate limiting
            except Exception as e:
                logger.error(f"❌ Errore per settore {sector}: {str(e)}")
        
        if performance_data:
            performance_df = pd.DataFrame(performance_data)
            logger.info(f"✅ Raccolti dati performance per {len(performance_df)} settori")
            return performance_df
        else:
            return None
            
    except Exception as e:
        logger.error(f"❌ Errore durante la raccolta dati settoriali: {str(e)}")
        return None

def process_all_data():
    """Elabora tutti i tipi di dati per tutti i simboli."""
    logger.info(f"Inizio raccolta comprensiva di dati per {len(SYMBOLS)} simboli")
    
    # Connessione database
    try:
        engine = get_db_engine()
        db_available = True
        logger.info("✅ Connessione al database stabilita")
    except Exception as e:
        logger.warning(f"⚠️ Database non disponibile: {str(e)}")
        logger.warning("⚠️ I dati saranno salvati solo localmente")
        db_available = False
        engine = None
    
    # 1. Dati di mercato
    for symbol in SYMBOLS:
        market_data = get_market_data_from_yahoo(symbol)
        if market_data is not None:
            # Salva nel database
            if db_available:
                success = save_dataframe_to_db(market_data, "stock_daily_prices", engine)
                if success:
                    logger.info(f"✅ Dati di mercato per {symbol} salvati nel database")
            
            # Salva su file
            market_data.to_csv(f"data/{symbol}_market_data.csv")
            time.sleep(random.uniform(1, 3))  # Previeni rate limiting
    
    # 2. Dati fondamentali
    for symbol in SYMBOLS:
        fundamental_data = get_fundamental_data(symbol)
        for data_type, data in fundamental_data.items():
            if data is not None and not data.empty:
                # Salva nel database
                if db_available:
                    table_name = f"fundamental_{data_type}"
                    success = save_dataframe_to_db(data, table_name, engine)
                    if success:
                        logger.info(f"✅ Dati fondamentali {data_type} per {symbol} salvati nel database")
                
                # Salva su file
                data.to_csv(f"data/{symbol}_fundamental_{data_type}.csv")
        
        time.sleep(random.uniform(2, 5))  # Previeni rate limiting
    
    # 3. Dati macroeconomici
    macro_data = get_macroeconomic_data()
    for indicator, data in macro_data.items():
        if data is not None and not data.empty:
            # Salva nel database
            if db_available:
                success = save_dataframe_to_db(data, "macroeconomic_data", engine)
                if success:
                    logger.info(f"✅ Dati macroeconomici {indicator} salvati nel database")
            
            # Salva su file
            data.to_csv(f"data/macro_{indicator}.csv")
    
    # 4. Performance settoriale (analisi qualitativa)
    sector_performance = get_sector_performance()
    if sector_performance is not None:
        # Salva nel database
        if db_available:
            success = save_dataframe_to_db(sector_performance, "sector_performance", engine)
            if success:
                logger.info("✅ Dati di performance settoriale salvati nel database")
        
        # Salva su file
        sector_performance.to_csv("data/sector_performance.csv")
    
    # 5. News e sentiment (analisi qualitativa)
    for symbol in SYMBOLS:
        news_data = get_news_sentiment(symbol)
        if news_data is not None and not news_data.empty:
            # Salva nel database
            if db_available:
                success = save_dataframe_to_db(news_data, "news_sentiment", engine)
                if success:
                    logger.info(f"✅ Dati news per {symbol} salvati nel database")
            
            # Salva su file
            news_data.to_csv(f"data/{symbol}_news.csv")
            
        time.sleep(random.uniform(2, 5))  # Previeni rate limiting
    
    # 6. Dati opzioni (solo per simboli principali)
    for symbol in SYMBOLS[:3]:  # Limita ai primi 3 per risparmiare risorse
        options_data = get_options_data(symbol)
        if options_data is not None and not options_data.empty:
            # Salva nel database
            if db_available:
                success = save_dataframe_to_db(options_data, "options_data", engine)
                if success:
                    logger.info(f"✅ Dati opzioni per {symbol} salvati nel database")
            
            # Salva su file
            options_data.to_csv(f"data/{symbol}_options.csv")
            
        time.sleep(random.uniform(2, 5))  # Previeni rate limiting

if __name__ == "__main__":
    logger.info("🚀 Avvio raccolta dati comprensiva")
    
    # Installa dipendenze mancanti, se necessario
    missing_deps = []
    for module in ['yfinance', 'bs4', 'fredapi']:
        try:
            __import__(module)
        except ImportError:
            missing_deps.append(module)
    
    if missing_deps:
        logger.info(f"📦 Installazione dipendenze mancanti: {', '.join(missing_deps)}...")
        os.system(f"pip install {' '.join(missing_deps)}")
        logger.info("✅ Dipendenze installate")
    
    # Esegui la raccolta dati
    process_all_data()
    
    logger.info("✅ Raccolta dati comprensiva completata")
