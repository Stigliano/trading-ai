from sqlalchemy import create_engine
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_engine():
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASSWORD')
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")

    if not all([db_user, os.getenv('DB_PASSWORD'), db_name, host]):
        raise ValueError("❌ Configurazione database non valida o incompleta!")

    engine = create_engine(f"postgresql://{db_user}:{db_password}@{host}:{port}/{db_name}")
    return engine

def save_dataframe_to_db(df, table_name, engine):
    df.to_sql(table_name, con=engine, if_exists='append', index=True)

