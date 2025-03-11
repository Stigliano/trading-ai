# Usa l'ultima versione stabile di Python
FROM python:3.9-slim

# Argomento per specificare quale servizio costruire
ARG SERVICE_TYPE=api

# Imposta variabili di ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Imposta la directory di lavoro
WORKDIR /app

# Installa le dipendenze di sistema essenziali
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia prima solo requirements.txt per sfruttare la cache di Docker
COPY requirements.txt .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Crea le directory necessarie
RUN mkdir -p /app/api/model /app/scripts /app/logs /app/data

# Copia i file del progetto mantenendo la struttura
COPY . /app

# Assicurati che il modello sia nella posizione corretta
# Se il modello non è disponibile, crea un modello vuoto di base
RUN if [ ! -f "/app/api/model/xgboost_model.pkl" ]; then \
    echo "Modello non trovato, creazione di un modello di base..." && \
    python -c "import xgboost as xgb; import numpy as np; import joblib; \
    model = xgb.XGBRegressor(); X = np.random.rand(100, 5); y = np.random.rand(100); \
    model.fit(X, y); joblib.dump(model, '/app/api/model/xgboost_model.pkl')"; \
    fi

# Rendi eseguibili gli script
RUN if [ -d "/app/scripts" ]; then chmod +x /app/scripts/*.py; fi

# Esponi la porta 8080 per Cloud Run
EXPOSE 8080

# Avvia l'applicazione con Gunicorn e Uvicorn
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "api.main:app", "--bind", "0.0.0.0:8080"]
