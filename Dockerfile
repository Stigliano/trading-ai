# Usa Python 3.9 come immagine base
FROM python:3.9

# Imposta la working directory
WORKDIR /app

# Copia tutti i file locali nella directory di lavoro nel container
COPY . /app

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# 🔹 Genera automaticamente il modello xgboost_model.pkl durante la build
RUN python3 -c "  
import joblib;  
import xgboost as xgb;  
import numpy as np;  
model = xgb.XGBClassifier();  
X_sample = np.random.rand(10, 5);  
y_sample = np.random.randint(0, 2, 10);  
model.fit(X_sample, y_sample);  
joblib.dump(model, 'xgboost_model.pkl');  
print('✅ Modello xgboost_model.pkl generato con successo!');  
"

# Espone la porta 8080 per Cloud Run
EXPOSE 8080

# Comando di avvio del server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
