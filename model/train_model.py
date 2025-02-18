import xgboost as xgb
import pandas as pd
import joblib

data = pd.read_csv("market_data.csv")
X = data[["SMA_50", "SMA_200", "RSI", "ATR", "VWAP"]]
y = data["future_return"]

model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6)
model.fit(X, y)

joblib.dump(model, "xgboost_model.pkl")
