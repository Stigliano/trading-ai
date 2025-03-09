# Usa Python 3.9 come immagine base
FROM python:3.9

# Imposta la working directory
WORKDIR /app

# Copia tutti i file locali nella directory di lavoro nel container
COPY . /app

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copia e genera il modello XGBoost
COPY scripts/generate_model.py /app/scripts/generate_model.py
RUN python3 /app/scripts/generate_model.py

# Espone la porta 8080 per Cloud Run
EXPOSE 8080

# Comando di avvio del server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]

