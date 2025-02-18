# Aggiungere il codice nei file principali

echo 'import xgboost as xgb
import pandas as pd
import joblib

data = pd.read_csv("market_data.csv")
X = data[["SMA_50", "SMA_200", "RSI", "ATR", "VWAP"]]
y = data["future_return"]

model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6)
model.fit(X, y)

joblib.dump(model, "xgboost_model.pkl")' > model/train_model.py


echo 'import numpy as np
import gym
from stable_baselines3 import PPO

class TradingEnv(gym.Env):
    def __init__(self):
        self.action_space = gym.spaces.Discrete(3)
        self.observation_space = gym.spaces.Box(low=-1, high=1, shape=(5,), dtype=np.float32)
        self.state = np.zeros(5)

    def reset(self):
        self.state = np.random.uniform(-1, 1, 5)
        return self.state

    def step(self, action):
        reward = np.random.randn()
        self.state = np.random.uniform(-1, 1, 5)
        return self.state, reward, False, {}

env = TradingEnv()
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=10000)

model.save("rl_model")' > model/reinforcement_learning.py


echo 'from fastapi import FastAPI
import joblib
import numpy as np
from stable_baselines3 import PPO

app = FastAPI()

xgb_model = joblib.load("xgboost_model.pkl")
rl_model = PPO.load("rl_model")

@app.post("/predict")
def predict(data: dict):
    features = np.array([data["SMA_50"], data["SMA_200"], data["RSI"], data["ATR"], data["VWAP"]]).reshape(1, -1)
    market_prediction = xgb_model.predict(features)[0]
    action, _ = rl_model.predict(features)
    decision = ["BUY", "HOLD", "SELL"][action]

    return {"market_prediction": market_prediction, "trading_decision": decision}' > api/main.py


echo 'provider "google" {
  project = "trading-ai-project"
  region  = "us-central1"
}

resource "google_compute_instance" "trading_ai" {
  name         = "trading-ai-instance"
  machine_type = "n1-standard-2"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "ubuntu-2004-focal-v20230606"
      size  = 50
      type  = "pd-balanced"
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }
}' > terraform/main.tf


echo 'FROM python:3.9

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]' > docker/Dockerfile


echo 'fastapi
uvicorn
joblib
numpy
xgboost
pandas
stable-baselines3
gym' > docker/requirements.txt


echo '__pycache__/
*.pyc
*.pyo
*.pyd
*.log
*.sqlite3
venv/' > .gitignore
