from fastapi import FastAPI
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

    return {"market_prediction": market_prediction, "trading_decision": decision}
