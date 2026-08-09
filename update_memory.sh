#!/bin/bash
# update_memory.sh — Memory-Dateien mit dem Repo abgleichen
#
#   bash update_memory.sh                      # nur pullen
#   bash update_memory.sh --push               # pullen, dann lokale .md-Dateien pushen
#   bash update_memory.sh --push /pfad/zu/mds  # mit abweichendem Quellverzeichnis
#
# Gedacht fuer die PRIVATE Kopie: dort liegen die echten Memory-Module.
# Im oeffentlichen Template stehen in memory/ nur Blanko-Vorlagen.

set -uo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
MEMORY_DIR="$REPO_DIR/memory"
LOCAL_MEMORY="${2:-$HOME/Documents/memory}"

cd "$REPO_DIR" || exit 1

# --- PULL ---
echo "Hole aktuellen Stand von GitHub..."
if ! git pull --quiet origin main; then
    echo "FEHLER: git pull fehlgeschlagen. Konflikte pruefen."
    exit 1
fi

echo "Memory aktuell:"
for f in "$MEMORY_DIR"/*.md; do
    [ -e "$f" ] && echo "  - $(basename "$f")"
done

# --- OPTIONALER PUSH nach lokaler Bearbeitung ---
if [ "${1:-}" = "--push" ]; then
    echo ""

    if [ ! -d "$LOCAL_MEMORY" ]; then
        echo "FEHLER: Quellverzeichnis '$LOCAL_MEMORY' existiert nicht."
        echo "Pfad als zweites Argument uebergeben: bash update_memory.sh --push /pfad/zu/mds"
        exit 1
    fi

    if ! compgen -G "$LOCAL_MEMORY/*.md" > /dev/null; then
        echo "FEHLER: keine .md-Dateien in '$LOCAL_MEMORY'."
        exit 1
    fi

    echo "Kopiere .md-Dateien aus '$LOCAL_MEMORY' nach memory/ ..."
    cp "$LOCAL_MEMORY"/*.md "$MEMORY_DIR"/

    git add memory/
    CHANGED=$(git diff --cached --name-only)

    if [ -z "$CHANGED" ]; then
        echo "Keine Aenderungen — nichts zu pushen."
    else
        echo "Geaenderte Dateien:"
        echo "$CHANGED"
        git commit -m "memory: Update $(date +'%Y-%m-%d %H:%M')"
        git push origin main
        echo "Gepusht."
    fi
fi
