#!/bin/bash

# Configurazioni
REPO_DIR="$(pwd)"
LOG_DIR="$REPO_DIR/.github/log"
LOG_FILE="$LOG_DIR/github-actions-log.txt"
GITHUB_REPO="Stigliano/trading-ai"
GITHUB_BRANCH="main"
GCLOUD_PROJECT="trading90"
SERVICE_NAME="trading-ai-service"
REGION="us-central1"

# Crea cartella log se non esiste
mkdir -p "$LOG_DIR"

echo -e "\n🚀 Inizio deploy: $(date)" | tee -a "$LOG_FILE"

# Controlla se il deploy è eseguito in locale o in GitHub Actions
if [ -z "$GITHUB_ACTIONS" ]; then
  echo "🌐 Ambiente locale rilevato: eseguo commit e push."
  cd "$REPO_DIR" || exit 1

  git add .
  git commit -m "Auto-deploy: $(date)" && echo "✅ Commit effettuato con successo." || { echo "❌ Errore nel commit!"; exit 1; }
  git push origin "$GITHUB_BRANCH" && echo "✅ Push su GitHub completato." || { echo "❌ Errore nel push!"; exit 1; }

  echo -e "\n📡 Monitoraggio GitHub Actions..."
  sleep 5
  GH_RUN_ID=$(gh run list -R "$GITHUB_REPO" --branch "$GITHUB_BRANCH" --limit 1 --json databaseId --jq '.[0].databaseId')

  if [ -z "$GH_RUN_ID" ]; then
    echo "❌ Nessun workflow attivato su GitHub Actions!" | tee -a "$LOG_FILE"
    exit 1
  fi

  echo "🔄 In attesa del completamento del workflow ID: $GH_RUN_ID..."
  gh run watch "$GH_RUN_ID" -R "$GITHUB_REPO" || { echo "❌ Errore nel monitoraggio GitHub Actions!" | tee -a "$LOG_FILE"; exit 1; }

  gh run view "$GH_RUN_ID" --log -R "$GITHUB_REPO" | tee "$LOG_FILE"
else
  echo -e "\n🔄 GitHub Actions in corso, salto commit e push."
fi

# Deploy su Google Cloud Run
echo -e "\n🚀 Deploy su Google Cloud Run in corso..."
gcloud run deploy "$SERVICE_NAME" \
    --project="$GCLOUD_PROJECT" \
    --region="$REGION" \
    --allow-unauthenticated \
    --source="$REPO_DIR" \
    | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
  echo "✅ Deploy completato con successo!" | tee -a "$LOG_FILE"
else
  echo "❌ Errore durante il deploy su Google Cloud Run!" | tee -a "$LOG_FILE"
  exit 1
fi

echo -e "\n✅ Processo completato! Log disponibile in: $LOG_FILE"

