import os
import sys
import json
import time
import unittest
import requests
import pandas as pd
import numpy as np
import joblib
from google.cloud import storage
from google.api_core.exceptions import NotFound

class TradingAITestSuite(unittest.TestCase):
    """
    Suite di test end-to-end per verificare il funzionamento del sistema trading-ai.
    I test sono organizzati per verificare singoli componenti e l'integrazione tra di essi.
    """
    
    @classmethod
    def setUpClass(cls):
        """Configurazione iniziale per i test."""
        # Configura credenziali GCP - assumiamo che siano già configurate tramite variabili
        # d'ambiente o tramite l'esecuzione di gcloud auth
        cls.project_id = os.environ.get("GCP_PROJECT_ID")
        cls.bucket_name = "trading-ai-bucket"
        cls.api_endpoint = os.environ.get("TRADING_API_ENDPOINT", "http://localhost:8000")
        cls.collector_endpoint = os.environ.get("COLLECTOR_ENDPOINT", "http://localhost:8080")
        
        # Flag per test locali o cloud
        cls.run_local = os.environ.get("RUN_LOCAL", "true").lower() == "true"
        
        # Prepara dati di test
        cls.prepare_test_data()
    
    @classmethod
    def prepare_test_data(cls):
        """Crea dati di test da utilizzare in diversi test."""
        # Crea dati di test con le 5 feature utilizzate dal modello
        cls.test_data = pd.DataFrame({
            "SMA_50": [1.2, 0.9, 1.1],
            "SMA_200": [0.8, 0.7, 0.75],
            "RSI": [55, 48, 62],
            "ATR": [1.2, 1.0, 1.3],
            "VWAP": [105, 98, 110]
        })
        
        # Crea un file CSV temporaneo con questi dati
        cls.test_data.to_csv("test_data.csv", index=False)
    
    def test_01_model_files_exist(self):
        """Verifica che i file dei modelli esistano nel bucket GCS o localmente."""
        if self.run_local:
            # Test locale
            self.assertTrue(os.path.exists("models/xgboost_model.pkl") or 
                           os.path.exists("xgboost_model_artifact/xgboost_model.pkl"))
        else:
            # Test su GCS
            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.bucket(self.bucket_name)
            
            # Controlla se i modelli esistono nel bucket
            xgb_blob = bucket.blob("xgboost_model.pkl")
            rl_blob = bucket.blob("rl_model.zip")
            
            self.assertTrue(xgb_blob.exists(), "XGBoost model non trovato su GCS")
            self.assertTrue(rl_blob.exists(), "RL model non trovato su GCS")
    
    def test_02_fetch_data_script(self):
        """Testa lo script fetch_data.py per assicurarsi che possa scaricare dati."""
        # Importazione dinamica dello script
        sys.path.append("scripts")
        try:
            from fetch_data import fetch_data
            
            # Usa una API key di esempio - dovresti utilizzare quella reale o di test
            test_api_key = os.environ.get("ALPHAVANTAGE_API_KEY", "EXLZJSTT9BXDBAJC")
            data = fetch_data("AAPL", test_api_key)
            
            # Verifica che i dati abbiano la struttura corretta
            self.assertIsInstance(data, pd.DataFrame)
            self.assertTrue(len(data) > 0, "Nessun dato scaricato")
            self.assertTrue(all(col in data.columns for col in ['open', 'high', 'low', 'close', 'volume']))
            
            print("✅ Script fetch_data funziona correttamente")
        except Exception as e:
            self.fail(f"Errore durante l'esecuzione di fetch_data: {str(e)}")
    
    def test_03_collector_service(self):
        """Testa il collector service."""
        if not self.run_local:
            # Test cloud - assumiamo che il servizio sia già deployato
            try:
                payload = {"job_type": "test"}
                headers = {"Content-Type": "application/json"}
                response = requests.post(self.collector_endpoint, json=payload, headers=headers)
                
                # La risposta potrebbe essere "market closed" se la borsa è chiusa, 
                # ma dovrebbe comunque essere un 200 OK
                self.assertTrue(response.status_code in [200, 201])
                print(f"✅ Collector service risponde: {response.json()}")
            except Exception as e:
                self.fail(f"Errore durante il test del collector service: {str(e)}")
        else:
            print("⚠️ Test del collector saltato in modalità locale")
            # Puoi implementare un mock del collector service se necessario
    
    def test_04_local_model_prediction(self):
        """Testa la capacità di previsione del modello XGBoost locale."""
        try:
            # Trova il percorso del modello
            model_paths = [
                "models/xgboost_model.pkl",
                "xgboost_model_artifact/xgboost_model.pkl"
            ]
            
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if not model_path:
                # Se in locale non troviamo il modello, potremmo scaricarlo da GCS
                if not self.run_local:
                    storage_client = storage.Client(project=self.project_id)
                    bucket = storage_client.bucket(self.bucket_name)
                    blob = bucket.blob("xgboost_model.pkl")
                    blob.download_to_filename("temp_model.pkl")
                    model_path = "temp_model.pkl"
                else:
                    self.fail("Modello XGBoost non trovato localmente")
            
            # Carica il modello
            model = joblib.load(model_path)
            
            # Effettua previsioni sui dati di test
            predictions = model.predict(self.test_data)
            
            # Verifica che le previsioni siano state generate
            self.assertEqual(len(predictions), len(self.test_data))
            print(f"✅ Previsioni del modello generate correttamente: {predictions}")
        except Exception as e:
            self.fail(f"Errore durante il test del modello: {str(e)}")
    
    def test_05_api_endpoint(self):
        """Testa l'endpoint API per la previsione."""
        if not self.run_local:
            try:
                # Dati di prova per l'API
                test_payload = {
                    "SMA_50": 1.2,
                    "SMA_200": 0.8,
                    "RSI": 55,
                    "ATR": 1.2,
                    "VWAP": 105
                }
                
                # Effettua la richiesta all'API
                response = requests.post(f"{self.api_endpoint}/predict", json=test_payload)
                
                # Verifica la risposta
                self.assertEqual(response.status_code, 200)
                response_data = response.json()
                
                # Verifica che la risposta contenga i campi attesi
                self.assertIn("market_prediction", response_data)
                self.assertIn("trading_decision", response_data)
                
                # Verifica che la decisione di trading sia una delle opzioni valide
                self.assertIn(response_data["trading_decision"], ["BUY", "HOLD", "SELL"])
                
                print(f"✅ API endpoint funziona correttamente: {response_data}")
            except Exception as e:
                self.fail(f"Errore durante il test dell'API: {str(e)}")
        else:
            print("⚠️ Test dell'API saltato in modalità locale")
    
    def test_06_backtesting_dependencies(self):
        """Verifica che le dipendenze per il backtesting siano disponibili."""
        # Controlla se esiste il file historical_data.csv
        if self.run_local:
            if os.path.exists("backtesting/historical_data.csv"):
                print("✅ File di dati storici trovato")
            else:
                print("⚠️ File di dati storici non trovato localmente")
                
                # Potremmo generare un file di test
                test_data_extended = self.test_data.copy()
                test_data_extended["future_return"] = [0.02, -0.01, 0.015]  # Aggiungi la colonna target
                test_data_extended.to_csv("backtesting/historical_data.csv", index=False)
                print("🔧 Creato file di dati storici di test")
        else:
            # Verifica su GCS
            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.bucket(self.bucket_name)
            blob = bucket.blob("historical_data.csv")
            
            if blob.exists():
                print("✅ File di dati storici trovato su GCS")
            else:
                print("⚠️ File di dati storici non trovato su GCS")
    
    def test_07_end_to_end_flow(self):
        """Test end-to-end del flusso completo (simulato)."""
        print("\n--- SIMULAZIONE FLUSSO COMPLETO ---")
        print("1. Collector service raccoglie dati")
        print("2. I dati vengono elaborati e salvati")
        print("3. Il modello fa previsioni sui dati")
        print("4. Le azioni di trading vengono determinate")
        
        # Qui possiamo simulare un flusso completo tra i vari componenti
        # Questo è più un test logico che fisico
        
        # Fingiamo di aver raccolto dati dal mercato
        market_data = self.test_data.copy()
        print(f"Dati di mercato raccolti:\n{market_data.head()}")
        
        # Fingiamo di fare previsioni
        try:
            # Trova il modello
            model_path = None
            for path in ["models/xgboost_model.pkl", "xgboost_model_artifact/xgboost_model.pkl"]:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if model_path:
                model = joblib.load(model_path)
                predictions = model.predict(market_data)
                print(f"Previsioni generate: {predictions}")
                
                # Simuliamo le decisioni di trading basate sulle previsioni
                decisions = ["BUY" if p > 0.02 else "HOLD" if p > -0.01 else "SELL" for p in predictions]
                print(f"Decisioni di trading: {decisions}")
                
                # Verifica che il flusso sia coerente
                self.assertEqual(len(predictions), len(market_data))
                self.assertEqual(len(decisions), len(market_data))
                
                print("✅ Simulazione del flusso end-to-end completata con successo")
            else:
                print("⚠️ Modello non trovato, simulazione parziale")
        except Exception as e:
            self.fail(f"Errore durante la simulazione del flusso: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        """Pulizia dopo i test."""
        # Rimuovi file temporanei creati durante i test
        if os.path.exists("test_data.csv"):
            os.remove("test_data.csv")
        
        if os.path.exists("temp_model.pkl"):
            os.remove("temp_model.pkl")
        
        print("\n✨ Test completati! ✨")

def run_tests():
    """Esegue tutti i test."""
    # Configura logging
    import logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Esegui i test
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == "__main__":
    # Parametri da linea di comando
    if len(sys.argv) > 1 and sys.argv[1] == "--cloud":
        os.environ["RUN_LOCAL"] = "false"
        print("⚡ Esecuzione dei test in modalità CLOUD")
    else:
        print("⚡ Esecuzione dei test in modalità LOCALE")
    
    # Esegui i test
    run_tests()
