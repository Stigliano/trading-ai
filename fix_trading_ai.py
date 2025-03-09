import os
import subprocess

# Definisci le cartelle e i file da modificare
PROJECT_DIR = os.path.expanduser("~/trading-ai")
API_DIR = os.path.join(PROJECT_DIR, "api")
MODEL_DIR = os.path.join(API_DIR, "model")
MAIN_PY = os.path.join(API_DIR, "main.py")
DOCKERFILE = os.path.join(PROJECT_DIR, "Dockerfile")
CLOUDBUILD_YAML = os.path.join(PROJECT_DIR, "cloudbuild.yaml")
REQUIREMENTS_TXT = os.path.join(PROJECT_DIR, "requirements.txt")

# Assicura che le cartelle esistano
os.makedirs(MODEL_DIR, exist_ok=True)

# 1️⃣ CREA O MODIFICA api/main.py
main_py_code = '''import os
import joblib
from fastapi import FastAPI

# Percorso del modello
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "xgboost_model.pkl")

app = FastAPI()

# Verifica che il modello esista prima di caricarlo
if os.path.exists(MODEL_PATH):
    xgb_model = joblib.load(MODEL_PATH)
    print("✅ Modello caricato con successo!")
else:
    raise FileNotFoundError(f"❌ Errore: Il file '{MODEL_PATH}' non è stato trovato.")

@app.get("/")
async def root():
    return {"message": "Trading AI API is running!"}
'''

with open(MAIN_PY, "w") as f:
    f.write(main_py_code)
print("✅ Modificato api/main.py")

# 2️⃣ CREA O MODIFICA Dockerfile
dockerfile_code = '''# Usa l'ultima versione stabile di Python
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
'''

with open(DOCKERFILE, "w") as f:
    f.write(dockerfile_code)
print("✅ Modificato Dockerfile")

# 3️⃣ CREA O MODIFICA cloudbuild.yaml
cloudbuild_yaml_code = '''steps:
  # Step 1: Build dell'immagine Docker
  - name: "gcr.io/cloud-builders/docker"
    args: ["build", "-t", "us-central1-docker.pkg.dev/$PROJECT_ID/trading-ai-repo/trading-ai-service:latest", "."]

  # Step 2: Push dell'immagine nel Container Registry
  - name: "gcr.io/cloud-builders/docker"
    args: ["push", "us-central1-docker.pkg.dev/$PROJECT_ID/trading-ai-repo/trading-ai-service:latest"]

  # Step 3: Deploy su Cloud Run
  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: gcloud
    args:
      - "run"
      - "deploy"
      - "trading-ai-service"
      - "--image=us-central1-docker.pkg.dev/$PROJECT_ID/trading-ai-repo/trading-ai-service:latest"
      - "--region=$_REGION"
      - "--platform=managed"
      - "--allow-unauthenticated"
      - "--port=8080"

images:
  - "us-central1-docker.pkg.dev/$PROJECT_ID/trading-ai-repo/trading-ai-service:latest"

substitutions:
  _PROJECT_ID: "trading90"
  _REGION: "us-central1"
'''

with open(CLOUDBUILD_YAML, "w") as f:
    f.write(cloudbuild_yaml_code)
print("✅ Modificato cloudbuild.yaml")

# 4️⃣ CREA O MODIFICA requirements.txt
requirements_code = '''fastapi
uvicorn
gunicorn
joblib
xgboost
'''

with open(REQUIREMENTS_TXT, "w") as f:
    f.write(requirements_code)
print("✅ Modificato requirements.txt")

# 5️⃣ ESEGUE I COMANDI GIT E GOOGLE CLOUD BUILD
commands = [
    ["git", "add", "."],
    ["git", "commit", "-m", "Fix: Risolto problema modello e avvio servizio"],
    ["git", "push", "origin", "main"],
    [
        "gcloud", "builds", "submit", 
        "--config=cloudbuild.yaml", 
        "--substitutions=_PROJECT_ID=trading90,_REGION=us-central1"
    ]
]

for cmd in commands:
    try:
        subprocess.run(cmd, check=True, cwd=PROJECT_DIR)
        print(f"✅ Comando eseguito: {' '.join(cmd)}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore eseguendo: {' '.join(cmd)}")
        print(e)
