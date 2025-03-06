import pandas as pd
import numpy as np
import joblib
from stable_baselines3 import PPO
from google.cloud import storage
from sklearn.metrics import mean_squared_error

BUCKET_NAME = "trading-ai-bucket"

def download_from_gcs(bucket_name, source_blob_name, destination_file_name):
    """Scarica un file da Google Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    print(f"✔ Scaricato {source_blob_name} da {bucket_name} a {destination_file_name}")

class Backtesting:
    def __init__(self, data_file="historical_data.csv"):
        # Scarica i dati e i modelli da Google Cloud Storage
        download_from_gcs(BUCKET_NAME, "historical_data.csv", "historical_data.csv")
        download_from_gcs(BUCKET_NAME, "xgboost_model.pkl", "xgboost_model.pkl")
        download_from_gcs(BUCKET_NAME, "rl_model.zip", "rl_model.zip")

        # Carica i dati e i modelli
        self.data = pd.read_csv(data_file)
        self.xgb_model = joblib.load("xgboost_model.pkl")
        self.rl_model = PPO.load("rl_model.zip")

    def compute_metrics(self, returns):
        sharpe_ratio = returns.mean() / returns.std()
        max_drawdown = np.min(returns)
        win_loss_ratio = (returns > 0).sum() / (returns < 0).sum()
        return {
            "Sharpe Ratio": sharpe_ratio,
            "Max Drawdown": max_drawdown,
            "Win/Loss Ratio": win_loss_ratio
        }

    def run(self):
        features = self.data[["SMA_50", "SMA_200", "RSI", "ATR", "VWAP"]]
        actual_returns = self.data["future_return"]

        predicted_returns = self.xgb_model.predict(features)
        action, _ = self.rl_model.predict(features.to_numpy())

        returns = predicted_returns * action
        metrics = self.compute_metrics(returns)

        print(f"✔ Backtesting Completed. Metrics: {metrics}")
        return metrics

if __name__ == "__main__":
    backtester = Backtesting()
    backtester.run()

