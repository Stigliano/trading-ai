#!/bin/bash

# Configura le variabili
TF_DIR="$HOME/trading-ai/terraform"

# Vai nella cartella Terraform
cd "$TF_DIR" || { echo "❌ Errore: Cartella Terraform non trovata"; exit 1; }

# Rimuove la vecchia configurazione di Terraform
echo "🗑️ Rimozione vecchia configurazione Terraform..."
rm -rf .terraform 

# Reinizializza Terraform
echo "🔄 Inizializzazione Terraform..."
terraform init

# Controlla se ci sono errori
echo "🔍 Verifica delle modifiche..."
terraform plan -out=tfplan

# Applica le modifiche con conferma automatica
echo "🚀 Applicazione delle modifiche Terraform..."
terraform apply "tfplan"

echo "✅ Deploy completato con successo!"

