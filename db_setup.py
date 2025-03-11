#!/usr/bin/env python3
"""
Script per configurare il database ricostruendo le tabelle.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_setup')

def main():
    """Funzione principale per eseguire la configurazione del database."""
    # Carica variabili d'ambiente
    load_dotenv()
    
    # Recupera le credenziali del database
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME')

    # Verifica se le credenziali sono disponibili
    if not all([db_user, db_password, db_host, db_name]):
        logger.error("❌ Credenziali database mancanti. Controlla il file .env")
        sys.exit(1)
    
    # Crea connessione al database
    try:
        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(connection_string)
        
        logger.info(f"Connessione a {db_name} su {db_host} stabilita")
        
        # Leggi lo script SQL
        with open('recreate_tables.sql', 'r') as file:
            sql_script = file.read()
        
        # Esegui lo script SQL
        with engine.begin() as conn:
            # Dividi lo script in comandi separati
            commands = sql_script.split(';')
            
            for cmd in commands:
                cmd = cmd.strip()
                if cmd:
                    logger.info(f"Esecuzione comando SQL: {cmd[:50]}...")
                    conn.execute(text(cmd))
        
        logger.info("✅ Configurazione del database completata con successo")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante la configurazione del database: {str(e)}")
        return False

if __name__ == "__main__":
    if main():
        print("\n✅ Database configurato correttamente!")
    else:
        print("\n❌ Configurazione database fallita. Controlla i log per dettagli.")
