# Usa l'ultima versione stabile di Python
FROM python:3.9

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file del progetto
COPY . /app

# Assicurati che la cartella model/ esista e copia il modello
RUN mkdir -p /app/api/model
COPY api/model/xgboost_model.pkl /app/api/model/xgboost_model.pkl

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta 8080 per Cloud Run
EXPOSE 8080

# Avvia l'applicazione con Gunicorn e Uvicorn
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "api.main:app", "--bind", "0.0.0.0:8080"]
