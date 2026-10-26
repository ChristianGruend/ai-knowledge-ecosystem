#!/bin/bash
set -euo pipefail

REPO_DIR="${AI_KNOWLEDGE_DATA_DIR:-$HOME/Projekte/ai-knowledge-data}"
LOG_FILE="$HOME/.local/share/ai-knowledge-sync.log"
CC_PROJECTS_DIR="$HOME/.claude/projects"
MIRROR_DIR="$REPO_DIR/claude-memories"
HERMES_MEMORIES_DIR="${HERMES_HOME:-$HOME/.hermes}/memories"
HERMES_MIRROR_DIR="$REPO_DIR/hermes-memories"

log() { echo "$*" >> "$LOG_FILE"; }

# Log auf die letzten 2000 Zeilen begrenzen
if [ -f "$LOG_FILE" ] && [ "$(wc -l < "$LOG_FILE")" -gt 2000 ]; then
    tail -n 2000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi

log "=== $(date '+%Y-%m-%d %H:%M:%S') ==="

cd "$REPO_DIR" || exit 1

# --- 1. Pull latest from GitHub ---
bash update_memory.sh >> "$LOG_FILE" 2>&1

# --- 2. Claude-Code-Memories ins Repo spiegeln ---
# Jedes ~/.claude/projects/<projekt>/memory/ landet unter claude-memories/<projekt>/
# (fuehrender Bindestrich weg, klein). --delete, damit geloeschte Memories verschwinden.
if [ -d "$CC_PROJECTS_DIR" ]; then
    mkdir -p "$MIRROR_DIR"
    shopt -s nullglob
    for src in "$CC_PROJECTS_DIR"/*/memory; do
        proj="$(basename "$(dirname "$src")")"
        name="$(echo "${proj#-}" | tr '[:upper:]' '[:lower:]')"
        mkdir -p "$MIRROR_DIR/$name"
        rsync -a --delete --include='*/' --include='*.md' --exclude='*' \
              "$src/" "$MIRROR_DIR/$name/" >> "$LOG_FILE" 2>&1
        log "Gespiegelt: $src -> claude-memories/$name/"
    done
    shopt -u nullglob
else
    log "Kein $CC_PROJECTS_DIR - Spiegelung uebersprungen."
fi

# --- 2b. Hermes-Memories (MEMORY.md, USER.md) ins Repo spiegeln ---
if [ -d "$HERMES_MEMORIES_DIR" ]; then
    mkdir -p "$HERMES_MIRROR_DIR"
    rsync -a --delete --include='*.md' --exclude='*' \
          "$HERMES_MEMORIES_DIR/" "$HERMES_MIRROR_DIR/" >> "$LOG_FILE" 2>&1
    log "Gespiegelt: $HERMES_MEMORIES_DIR -> hermes-memories/"
else
    log "Kein $HERMES_MEMORIES_DIR - Hermes-Spiegelung uebersprungen."
fi

# --- 3. Commit + Push, wenn sich etwas geaendert hat ---
if [ -n "$(git status --porcelain memory/ claude-memories/ hermes-memories/)" ]; then
    log "Aenderungen erkannt. Committe und pushe..."
    git add memory/ claude-memories/ hermes-memories/
    git commit -m "memory: auto-sync $(date '+%Y-%m-%d %H:%M')" >> "$LOG_FILE" 2>&1
    if git push origin main >> "$LOG_FILE" 2>&1; then
        log "Gepusht."
    else
        log "ERROR: git push fehlgeschlagen."
        exit 1
    fi
else
    log "No local changes to push."
fi

echo "" >> "$LOG_FILE"
