#!/bin/bash
# update_memory.sh – Memory-Dateien vom privaten Repo pullen
# Aufruf: bash update_memory.sh
# Optional: bash update_memory.sh --push  (nach lokaler Bearbeitung zurückpushen)

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
MEMORY_DIR="$REPO_DIR/memory"
# LOCAL_MEMORY: Pfad zu lokalen .md-Dateien, die gepusht werden sollen
# Kann als Argument übergeben werden: bash update_memory.sh --push /pfad/zu/dateien
LOCAL_MEMORY="${2:-$HOME/Documents/memory}"

cd "$REPO_DIR" || exit 1

# --- PULL ---
echo "Pulling latest memory from GitHub..."
git pull --quiet origin main

if [ $? -ne 0 ]; then
    echo "ERROR: git pull fehlgeschlagen. Konflikte prüfen."
    exit 1
fi

echo "Memory aktuell:"
ls "$MEMORY_DIR"/*.md | xargs -I{} basename {}

# --- OPTIONALER PUSH nach lokaler Bearbeitung ---
if [ "$1" = "--push" ]; then
    echo ""
    echo "Kopiere lokale .md-Dateien nach memory/..."
    cp "$LOCAL_MEMORY"/*.md "$MEMORY_DIR"/

    git add memory/
    CHANGED=$(git diff --cached --name-only)

    if [ -z "$CHANGED" ]; then
        echo "Keine Änderungen – nichts zu pushen."
    else
        echo "Geänderte Dateien:"
        echo "$CHANGED"
        DATUM=$(date +"%Y-%m-%d %H:%M")
        git commit -m "memory: Update $DATUM"
        git push origin main
        echo "Gepusht."
    fi
fi
