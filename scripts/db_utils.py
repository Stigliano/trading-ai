"""
Utility per la connessione e gestione del database PostgreSQL.
"""

import os
import logging
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, Table, Column, Integer, Float, String, DateTime, MetaData, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timedelta
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
    Se le credenziali non sono configurate, restituisce None.
    """
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME')

    # Verifica se i parametri del database sono stati forniti
    if not all([db_user, db_password, db_host, db_name]):
        logger.warning("⚠️ Configurazione database incompleta. Modalità file locale attivata.")
        return None

    # Se tutte le credenziali sono presenti, crea la connessione
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    logger.info(f"Creazione engine per database {db_name} su {db_host}")
    
    try:
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        logger.error(f"Errore nella creazione dell'engine: {str(e)}")
        return None

@contextmanager
def get_db_connection():
    """
    Context manager per la connessione al database.
    Gestisce la connessione e rilascia le risorse quando terminato.
    """
    engine = get_db_engine()
    connection = None
    try:
        if engine is None:
            logger.warning("⚠️ Engine del database non disponibile.")
            yield None
            return
            
        connection = engine.connect()
        logger.info("Connessione al database stabilita con successo.")
        yield connection
    except SQLAlchemyError as e:
        logger.error(f"Errore durante la connessione al database: {str(e)}")
        raise
    finally:
        if connection:
            connection.close()
            logger.info("Connessione al database chiusa.")

def normalize_dataframe_for_db(df):
    """
    Normalizza un DataFrame per renderlo compatibile con la struttura del database.
    """
    # Crea una copia per evitare modifiche all'originale
    normalized_df = df.copy()
    
    # Gestisci le colonne con indice multiplo
    if isinstance(normalized_df.columns, pd.MultiIndex):
        # Appiattisci le colonne multiindice
        normalized_df.columns = [f"{col[0]}_{col[1]}" if col[1] else col[0] for col in normalized_df.columns]
    
    # Mappa i nomi delle colonne alla struttura del database
    column_mappings = {
        # Mappa per stock_daily_prices
        'Date': 'date',
        'Datetime': 'datetime',
        'date_time': 'datetime',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume',
        'Symbol': 'symbol',
        'Source': 'source',
        
        # Per colonne con prefisso del simbolo
        'Open_SPY': 'open',
        'High_SPY': 'high',
        'Low_SPY': 'low',
        'Close_SPY': 'close',
        'Volume_SPY': 'volume',
        
        'Open_QQQ': 'open',
        'High_QQQ': 'high',
        'Low_QQQ': 'low',
        'Close_QQQ': 'close',
        'Volume_QQQ': 'volume',
        
        'Open_AAPL': 'open',
        'High_AAPL': 'high',
        'Low_AAPL': 'low',
        'Close_AAPL': 'close',
        'Volume_AAPL': 'volume',
        
        'Open_MSFT': 'open',
        'High_MSFT': 'high',
        'Low_MSFT': 'low',
        'Close_MSFT': 'close',
        'Volume_MSFT': 'volume',
        
        'Open_GOOGL': 'open',
        'High_GOOGL': 'high',
        'Low_GOOGL': 'low',
        'Close_GOOGL': 'close',
        'Volume_GOOGL': 'volume'
    }
    
    # Rinomina colonne basate sulla mappatura
    for old_name, new_name in column_mappings.items():
        if old_name in normalized_df.columns:
            normalized_df.rename(columns={old_name: new_name}, inplace=True)
    
    # Rimuovi colonne duplicate se presenti
    normalized_df = normalized_df.loc[:, ~normalized_df.columns.duplicated()]
    
    # Gestisci particolarità delle tabelle
    if 'date' not in normalized_df.columns and normalized_df.index.name in ['Date', 'date']:
        normalized_df.reset_index(inplace=True)
    
    return normalized_df


def prepare_market_data_for_db(df, symbol):
    """Prepara specificamente i dati di mercato per il database."""
    # Crea un nuovo DataFrame con le colonne corrette
    result_df = pd.DataFrame()
    
    # Estrai la data/datetime e assicurati che sia in formato datetime
    if df.index.name in ["Date", "date", "Datetime", "datetime", None] and isinstance(df.index, pd.DatetimeIndex):
        # L'indice è già un DatetimeIndex
        result_df["date"] = df.index
    elif "Date" in df.columns:
        result_df["date"] = pd.to_datetime(df["Date"])
    elif "date" in df.columns:
        result_df["date"] = pd.to_datetime(df["date"])
    else:
        # Crea una data utilizzando l'indice numerico
        start_date = datetime(2023, 1, 1)
        result_df["date"] = [start_date + timedelta(days=int(idx)) for idx in range(len(df))]
        logger.warning(f"Nessuna colonna data trovata per {symbol}, utilizzando date generate")
    
    # Mappa le colonne principali
    col_mapping = {
        "open": ["Open", f"Open_{symbol}", "open"],
        "high": ["High", f"High_{symbol}", "high"],
        "low": ["Low", f"Low_{symbol}", "low"],
        "close": ["Close", f"Close_{symbol}", "close"],
        "volume": ["Volume", f"Volume_{symbol}", "volume"]
    }
    
    for target_col, source_cols in col_mapping.items():
        for src_col in source_cols:
            if src_col in df.columns:
                result_df[target_col] = df[src_col]
                break
    
    # Assicurati che le colonne numeriche siano tipi di dati corretti
    numeric_cols = ["open", "high", "low", "close", "volume"]
    for col in numeric_cols:
        if col in result_df.columns:
            result_df[col] = pd.to_numeric(result_df[col], errors="coerce")
    
    # Aggiungi simbolo e fonte
    result_df["symbol"] = symbol
    if "source" in df.columns:
        result_df["source"] = df["source"]
    else:
        result_df["source"] = "yahoo_finance"
    
    # Aggiungi timestamp
    result_df["created_at"] = datetime.now()
    
    return result_df


def convert_series_to_float(value):
    """Converte un oggetto Series in float, se possibile."""
    if isinstance(value, pd.Series):
        if len(value) > 0:
            return float(value.iloc[0])
        return None
    return value

def clean_sector_performance_data(df):
    """Pulisce e prepara dati di performance settoriale per il database."""
    result_df = pd.DataFrame()
    
    # Estrai le informazioni e converti in tipi scalari
    result_df['date'] = df['date'].apply(lambda x: x if isinstance(x, datetime) else pd.to_datetime(x))
    result_df['sector'] = df['sector']
    result_df['etf'] = df['etf']
    
    # Converti Serie in valori float
    result_df['performance_1mo'] = df['performance_1mo'].apply(convert_series_to_float)
    
    # Aggiungi performance_3mo se presente, altrimenti imposta a None
    if 'performance_3mo' in df.columns:
        result_df['performance_3mo'] = df['performance_3mo'].apply(convert_series_to_float)
    else:
        result_df['performance_3mo'] = None
    
    result_df['last_price'] = df['last_price'].apply(convert_series_to_float)
    result_df['created_at'] = datetime.now()
    
    return result_df

def handle_table_specific_data(df_copy, table_name, engine):
    """Gestisce le operazioni specifiche per ciascuna tabella."""
    
    # Gestione speciale per dati di mercato
    if table_name == 'stock_daily_prices':
        try:
            # Determina il simbolo
            if 'symbol' in df_copy.columns:
                symbol = df_copy['symbol'].iloc[0]
            else:
                # Cerca di identificare il simbolo dalle colonne
                potential_symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL']
                for sym in potential_symbols:
                    if any(sym in col for col in df_copy.columns):
                        symbol = sym
                        break
                else:
                    symbol = 'UNKNOWN'
            
            # Prepara i dati
            prepared_df = prepare_market_data_for_db(df_copy, symbol)
            
            # Salva nel database con gestione dei duplicati
            # Utilizziamo l'approccio "on_conflict_do_nothing" per saltare i record duplicati
            with engine.connect() as connection:
                # Inserisce i dati ignorando i duplicati
                transaction = connection.begin()
                try:
                    # Costruisci una query che ignora i duplicati
                    insert_stmt = f"""
                    INSERT INTO {table_name} (date, open, high, low, close, volume, symbol, source, created_at)
                    VALUES (:date, :open, :high, :low, :close, :volume, :symbol, :source, :created_at)
                    ON CONFLICT (date, symbol) DO NOTHING
                    """
                    
                    # Converti DataFrame in lista di dict per l'inserimento
                    records = prepared_df.to_dict('records')
                    
                    # Inserisci un record alla volta per gestire meglio gli errori
                    inserted = 0
                    for record in records:
                        try:
                            connection.execute(text(insert_stmt), record)
                            inserted += 1
                        except Exception as e:
                            # Logga l'errore ma continua con gli altri record
                            logger.warning(f"Non è stato possibile inserire il record {record['date']}, {record['symbol']}: {str(e)}")
                    
                    transaction.commit()
                    logger.info(f"✅ {inserted} righe salvate nella tabella {table_name} (ignorati duplicati)")
                    return True
                except Exception as e:
                    transaction.rollback()
                    logger.error(f"❌ Errore durante il salvataggio con gestione dei duplicati: {str(e)}")
                    return False
        except Exception as e:
            logger.error(f"❌ Errore durante la preparazione dei dati di mercato: {str(e)}")
            return False
    
    # Gestione speciale per dati settoriali
    elif table_name == 'sector_performance':
        try:
            # Verifica che gli oggetti Series siano convertiti in float
            cleaned_df = clean_sector_performance_data(df_copy)
            
            # Salva nel database
            cleaned_df.to_sql(table_name, con=engine, if_exists='append', index=False)
            logger.info(f"✅ {len(cleaned_df)} righe salvate nella tabella {table_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Errore durante il salvataggio dei dati settoriali: {str(e)}")
            return False
    
    # Gestione speciale per dati fondamentali info
    elif table_name == 'fundamental_info':
        # Gestisci il caso speciale dei dati fondamentali info
        rows = []
        try:
            # Determina il simbolo
            if "symbol" in df_copy.columns:
                symbol = df_copy["symbol"].iloc[0]
            else:
                symbol = "UNKNOWN"
            
            # Appiattisci tutti i dati in coppie chiave-valore
            for _, row in df_copy.iterrows():
                # Gestisci lista di dizionari o dizionario singolo
                for col in row.index:
                    val = row[col]
                    # Salta symbol e created_at
                    if col in ["symbol", "created_at"]:
                        continue
                        
                    # Gestisci dizionari e liste annidati
                    if isinstance(val, dict):
                        # Appiattisci il dizionario
                        for k, v in val.items():
                            if v is not None and not pd.isna(v):
                                rows.append({
                                    "symbol": symbol,
                                    "key": f"{col}.{k}",
                                    "value": str(v),
                                    "created_at": datetime.now()
                                })
                    elif isinstance(val, list):
                        # Converti lista in stringa JSON
                        rows.append({
                            "symbol": symbol,
                            "key": col,
                            "value": str(val),
                            "created_at": datetime.now()
                        })
                    else:
                        # Valore semplice
                        if val is not None and not pd.isna(val):
                            rows.append({
                                "symbol": symbol,
                                "key": col,
                                "value": str(val),
                                "created_at": datetime.now()
                            })
            
            if rows:
                # Crea DataFrame con le righe appiattite
                info_df = pd.DataFrame(rows)
                # Salva nel database
                info_df.to_sql(table_name, con=engine, if_exists="append", index=False)
                logger.info(f"✅ {len(info_df)} righe salvate nella tabella {table_name}")
                return True
            else:
                logger.warning(f"⚠️ Nessun dato valido da salvare nella tabella {table_name}")
                return False
        except Exception as e:
            logger.error(f"❌ Errore durante il salvataggio dei dati fondamentali info: {str(e)}")
            return False
    
    # Gestione speciale per dati fondamentali finanziari
    elif table_name.startswith('fundamental_') and table_name != 'fundamental_info':
        # Assicurati che i dati siano nel formato corretto
        if not df_copy.empty:
            # Se non è già nel formato giusto, trasforma in formato lungo
            if len(df_copy.columns) > 5:  # Ha molte colonne, quindi probabilmente in formato ampio
                # Identifica colonne non numeriche
                try:
                    id_cols = ['symbol']
                    if 'date' in df_copy.columns:
                        id_cols.append('date')
                    
                    # Converti in formato lungo
                    melted_df = pd.melt(
                        df_copy, 
                        id_vars=id_cols,
                        var_name='metric',
                        value_name='value'
                    )
                    
                    # Filtra valori nulli
                    melted_df = melted_df.dropna(subset=['value'])
                    
                    # Converti valori in float dove possibile
                    melted_df['value'] = pd.to_numeric(melted_df['value'], errors='coerce')
                    
                    # Aggiungi timestamp
                    melted_df['created_at'] = datetime.now()
                    
                    if not melted_df.empty:
                        melted_df.to_sql(table_name, con=engine, if_exists='append', index=False)
                        logger.info(f"✅ {len(melted_df)} righe salvate nella tabella {table_name}")
                        return True
                except Exception as e:
                    logger.error(f"❌ Errore durante la trasformazione dei dati fondamentali: {str(e)}")
            else:
                # Già in formato corretto
                df_copy.to_sql(table_name, con=engine, if_exists='append', index=False)
                logger.info(f"✅ {len(df_copy)} righe salvate nella tabella {table_name}")
                return True
        return False
    
    # Gestione generica per tutte le altre tabelle
    else:
        df_copy.to_sql(table_name, con=engine, if_exists='append', index=False)
        logger.info(f"✅ {len(df_copy)} righe salvate nella tabella {table_name}")
        return True

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

    # Crea una copia del dataframe per evitare modifiche all'originale
    df_copy = df.copy()
    
    # Se non viene fornito un engine, ne crea uno nuovo
    close_engine = False
    if engine is None:
        try:
            engine = get_db_engine()
            close_engine = True
            if engine is None:
                logger.info(f"⚠️ Database non disponibile. Salvataggio solo su file.")
                # Assicurati che la directory data esista
                os.makedirs("data", exist_ok=True)
                # Salva su file CSV
                filename = f"data/{table_name}_{datetime.now().strftime('%Y%m%d')}.csv"
                df_copy.to_csv(filename, index=False)
                logger.info(f"✅ Dati salvati in {filename}")
                return True
        except Exception as e:
            logger.error(f"Errore nella creazione dell'engine: {str(e)}")
            return False
    
    try:
        # Normalizza il DataFrame per il database
        normalized_df = normalize_dataframe_for_db(df_copy)
        
        # Gestione specifica della tabella
        return handle_table_specific_data(normalized_df, table_name, engine)
        
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
            if conn is None:
                logger.warning("⚠️ Database non disponibile")
                return False
                
            # Esegui una query di test
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
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
            print("❌ Impossibile connettersi al database o database non configurato.")
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
