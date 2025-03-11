import joblib
import xgboost as xgb
import numpy as np

# Crea un modello XGBoost fittizio
model = xgb.XGBClassifier()
X_sample = np.random.rand(10, 5)
y_sample = np.random.randint(0, 2, 10)
model.fit(X_sample, y_sample)

# Salva il modello
model_path = "/app/xgboost_model.pkl"
joblib.dump(model, model_path)
print(f"✅ Modello salvato in {model_path}")
