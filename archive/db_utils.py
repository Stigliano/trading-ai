"""
Utility per la connessione e gestione del database PostgreSQL.
"""

import os
import logging
import pandas as pd
from sqlalchemy import create_engine, Table, Column, Integer, Float, String, DateTime, MetaData
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from dotenv import load_dotenv
from contextlib import contextmanager

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_utils')

# Carica variabili d'ambiente
load_dotenv()

def get_db_engine():
    """
    Crea e restituisce un engine SQLAlchemy per la connessione al database PostgreSQL.
    """
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME')

    if not all([db_user, db_password, db_host, db_name]):
        logger.error("❌ Configurazione database non valida o incompleta!")
        raise ValueError("❌ Configurazione database non valida o incompleta!")

    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    logger.info(f"Creazione engine per database {db_name} su {db_host}")
    
    try:
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        logger.error(f"Errore nella creazione dell'engine: {str(e)}")
        raise

# Schema del database
metadata = MetaData()

# Tabella per i dati di mercato giornalieri
stock_daily_prices = Table(
    'stock_daily_prices', 
    metadata,
    Column('id', Integer, primary_key=True),
    Column('date', DateTime, index=True),
    Column('symbol', String(20), index=True),
    Column('open', Float),
    Column('high', Float),
    Column('low', Float),
    Column('close', Float),
    Column('volume', Float),
    Column('created_at', DateTime, default=datetime.now)
)

# Tabella per i dati intraday
intraday_data = Table(
    'intraday_data', 
    metadata,
    Column('id', Integer, primary_key=True),
    Column('datetime', DateTime, index=True),
    Column('symbol', String(20), index=True),
    Column('interval', String(10)),  # 1min, 5min, 15min, 30min, 60min
    Column('open', Float),
    Column('high', Float),
    Column('low', Float),
    Column('close', Float),
    Column('volume', Float),
    Column('created_at', DateTime, default=datetime.now)
)

# Tabella per i dati fondamentali
fundamental_data = Table(
    'fundamental_data',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('symbol', String(20), index=True),
    Column('date', DateTime, index=True),
    Column('data_type', String(50)),  # income, balance, cashflow, etc.
    Column('metric', String(100)),
    Column('value', Float),
    Column('created_at', DateTime, default=datetime.now)
)

# Tabella per i dati macroeconomici
macroeconomic_data = Table(
    'macroeconomic_data',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('date', DateTime, index=True),
    Column('indicator', String(50), index=True),
    Column('name', String(100)),
    Column('value', Float),
    Column('created_at', DateTime, default=datetime.now)
)

@contextmanager
def get_db_connection():
    """
    Context manager per la connessione al database.
    Gestisce la connessione e rilascia le risorse quando terminato.
    """
    engine = get_db_engine()
    connection = None
    try:
        connection = engine.connect()
        logger.info("Connessione al database stabilita con successo.")
        
        # Crea tabelle se non esistono
        metadata.create_all(engine)
        logger.info("Schema del database verificato/creato.")
        
        yield connection
    except SQLAlchemyError as e:
        logger.error(f"Errore durante la connessione al database: {str(e)}")
        raise
    finally:
        if connection:
            connection.close()
            logger.info("Connessione al database chiusa.")

def save_dataframe_to_db(df, table_name, engine=None):
    """
    Salva un DataFrame nel database.
    
    Args:
        df (pandas.DataFrame): DataFrame con i dati da salvare
        table_name (str): Nome della tabella nel database
        engine (sqlalchemy.engine.Engine, optional): Engine SQLAlchemy. Se None, ne viene creato uno nuovo.
    
    Returns:
        bool: True se il salvataggio è avvenuto con successo, False altrimenti
    """
    if df is None or df.empty:
        logger.warning("DataFrame vuoto o None. Nessun dato da salvare.")
        return False

    # Se non viene fornito un engine, ne crea uno nuovo
    close_engine = False
    if engine is None:
        try:
            engine = get_db_engine()
            close_engine = True
        except Exception as e:
            logger.error(f"Errore nella creazione dell'engine: {str(e)}")
            return False
    
    try:
        # Controlla se ci sono colonne di tipo datetime nell'indice
        if df.index.name and pd.api.types.is_datetime64_any_dtype(df.index):
            # Conserva l'indice datetime come colonna
            df = df.reset_index()

        # Elimina eventuali colonne NaN
        df = df.dropna(axis=1, how='all')
        
        # Converti tipi di dati
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col])
                except ValueError:
                    pass  # Non è un dato numerico, lascialo come oggetto
        
        # Aggiungi timestamp di creazione se non presente
        if 'created_at' not in df.columns:
            df['created_at'] = datetime.now()
        
        # Aggiungi colonna symbol se manca e viene richiesto
        if 'symbol' not in df.columns and table_name in ['stock_daily_prices', 'intraday_data']:
            symbol = os.getenv('DEFAULT_SYMBOL', 'UNKNOWN')
            df['symbol'] = symbol
            logger.warning(f"Colonna 'symbol' mancante. Inserito valore di default: {symbol}")
        
        # Salva nel database
        df.to_sql(
            table_name, 
            con=engine, 
            if_exists='append', 
            index=False,
            method='multi'
        )
        
        logger.info(f"✅ {len(df)} righe salvate nella tabella {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante il salvataggio dei dati: {str(e)}")
        return False
        
    finally:
        if close_engine and engine:
            engine.dispose()

def check_db_connection():
    """
    Verifica la connessione al database.
    
    Returns:
        bool: True se la connessione è stata stabilita con successo, False altrimenti
    """
    try:
        with get_db_connection() as conn:
            result = conn.execute("SELECT 1").fetchone()
            if result and result[0] == 1:
                logger.info("✅ Connessione al database verificata con successo")
                return True
            else:
                logger.error("❌ Errore durante la verifica della connessione al database")
                return False
    except Exception as e:
        logger.error(f"❌ Errore durante la verifica della connessione al database: {str(e)}")
        return False

if __name__ == "__main__":
    # Test di connessione
    try:
        if check_db_connection():
            print("✅ Connessione al database stabilita con successo!")
        else:
            print("❌ Impossibile connettersi al database.")
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
