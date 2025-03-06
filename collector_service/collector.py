import os
import json
import datetime
import requests
import exchange_calendars as ecals
from google.cloud import storage
from flask import Flask, request, jsonify

# Configurazione Google Cloud Storage
STORAGE_BUCKET = "trading-ai-bucket"
storage_client = storage.Client()
bucket = storage_client.bucket(STORAGE_BUCKET)

app = Flask(__name__)

def is_market_open():
    """Verifica se il NYSE è aperto in base al calendario ufficiale."""
    try:
        nyse = ecals.get_calendar("XNYS")
        now = datetime.datetime.utcnow()

        print(f"🔍 Data attuale UTC: {now.date()}, Orario: {now.time()}")

        # Controlliamo se oggi è un giorno di trading
        if not nyse.is_session(now.date()):
            print("❌ Oggi non è un giorno di trading.")
            return False

        # Accediamo agli orari di apertura/chiusura in modo più sicuro
        trading_days = nyse.sessions_in_range(now.date(), now.date())

        if trading_days.empty:
            print("⚠️ Nessuna sessione trovata per oggi, il mercato è chiuso.")
            return False

        market_open = nyse.session_open(trading_days[0])
        market_close = nyse.session_close(trading_days[0])

        print(f"🕒 Apertura mercato: {market_open.time()}, Chiusura mercato: {market_close.time()}")

        if market_open.time() <= now.time() <= market_close.time():
            print("✅ La borsa è APERTA!")
            return True
        else:
            print("⏳ Fuori dall'orario di trading.")
            return False
    except Exception as e:
        print(f"⚠️ Errore nel controllo dell'apertura del mercato: {str(e)}")
        return False

def collect_and_store_data(job_type):
    """Raccoglie i dati di mercato e li salva su Google Cloud Storage."""
    if not is_market_open():
        return jsonify({"status": "skipped", "reason": "Market closed"}), 200

    print(f"🔄 Raccolta dati per {job_type} in corso...")

    # Simulazione di raccolta dati - qui devi inserire la tua API reale
    url = "https://api.example.com/marketdata"  # 🔴 Cambia con la tua API reale
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        filename = f"market_data/{job_type}_{datetime.datetime.utcnow().isoformat()}.json"
        
        # Salvataggio su Google Cloud Storage
        blob = bucket.blob(filename)
        blob.upload_from_string(json.dumps(data), content_type="application/json")
        
        print(f"✅ Dati salvati su GCS: {filename}")
        return jsonify({"status": "success", "job_type": job_type, "file": filename}), 200
    else:
        print(f"❌ Errore API: {response.status_code}")
        return jsonify({"status": "error", "message": "API request failed"}), 500

@app.route("/", methods=["POST"])
def handle_request():
    """Gestisce le richieste in arrivo dal Google Cloud Scheduler."""
    # Verifica se il Content-Type è corretto
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type, expected application/json"}), 415

    try:
        body = request.get_json()
        if not body:
            return jsonify({"error": "Empty request body"}), 400

        job_type = body.get("job_type", "unknown")
        print(f"🛠️ JOB_TYPE: {job_type} at {datetime.datetime.utcnow()}")
        return collect_and_store_data(job_type)

    except Exception as e:
        print(f"⚠️ Errore nel gestire la richiesta: {str(e)}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

