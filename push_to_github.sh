#!/bin/bash

# Nome del branch su cui lavorare (può essere modificato se usi branch diversi)
BRANCH="main"

# Messaggio di commit
echo "🔹 Inserisci un messaggio per il commit:"
read COMMIT_MSG

# Controlla se ci sono modifiche da commitare
if [[ -z $(git status --porcelain) ]]; then
    echo "✅ Nessuna modifica da commitare. Il repository è aggiornato."
    exit 0
fi

# Aggiunge tutti i file
echo "📂 Aggiungo le modifiche a Git..."
git add .

# Crea un commit con il messaggio inserito
echo "📝 Creazione del commit..."
git commit -m "$COMMIT_MSG"

# Esegui il pull prima di pushare per evitare conflitti
echo "🔄 Sincronizzazione con il repository remoto..."
git pull origin "$BRANCH" --rebase

# Esegui il push delle modifiche su GitHub
echo "🚀 Invio delle modifiche a GitHub..."
git push origin "$BRANCH"

# Controlla se il push è andato a buon fine
if [[ $? -eq 0 ]]; then
    echo "✅ Modifiche inviate con successo!"
else
    echo "❌ Errore durante il push. Controlla i messaggi sopra per ulteriori dettagli."
fi
