#!/bin/bash
# ai-knowledge-sync.sh – Memories aus Claude Code und Hermes ins private Repo spiegeln,
# Hermes-Profile angleichen, alles prüfen, committen und pushen.
#
#   ai-knowledge-sync.sh              voller Lauf (Timer + Path-Unit)
#   ai-knowledge-sync.sh --dry-run    nur anzeigen: kein Pull, kein Schreiben in Hermes, kein Commit/Push
#   ai-knowledge-sync.sh --debounce N vor dem Lauf N Sekunden warten (Path-Unit: Schreibserien bündeln)
set -euo pipefail

REPO_DIR="${AI_KNOWLEDGE_DATA_DIR:-$HOME/Projekte/ai-knowledge-data}"
LOG_FILE="$HOME/.local/share/ai-knowledge-sync.log"
STATE_DIR="${AI_KNOWLEDGE_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/ai-knowledge-sync}"
CC_PROJECTS_DIR="$HOME/.claude/projects"
MIRROR_DIR="$REPO_DIR/claude-memories"
HELPER="$REPO_DIR/scripts/hermes_memory.py"
PY="${AI_KNOWLEDGE_PYTHON:-$HOME/.hermes/hermes-agent/venv/bin/python}"
[ -x "$PY" ] || PY=python3

DRY_RUN=0
DEBOUNCE=0
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --debounce) DEBOUNCE="$2"; shift ;;
        *) echo "Unbekannte Option: $1" >&2; exit 2 ;;
    esac
    shift
done

mkdir -p "$STATE_DIR" "$(dirname "$LOG_FILE")"
if [ "$DRY_RUN" = 1 ]; then
    log() { echo "$*"; }
else
    log() { echo "$*" >> "$LOG_FILE"; }
fi

# Status für den Hermes-Dashboard-Tab „Memory“: result = ok | error
write_status() {
    [ "$DRY_RUN" = 1 ] && return 0
    local head ahead
    head="$(git -C "$REPO_DIR" log -1 --format='%h %cs %s' 2>/dev/null || true)"
    ahead="$(git -C "$REPO_DIR" rev-list --count origin/main..HEAD 2>/dev/null || echo '?')"
    "$PY" - "$STATE_DIR/status.json" "$1" "$2" "$head" "$ahead" <<'EOF'
import datetime, json, os, sys, tempfile
path, result, message, head, ahead = sys.argv[1:]
data = {"result": result, "message": message, "finished_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "last_commit": head, "unpushed_commits": ahead}
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
with os.fdopen(fd, "w") as fh:
    json.dump(data, fh, ensure_ascii=False, indent=2)
os.replace(tmp, path)
EOF
}

trap 'rc=$?; if [ $rc -ne 0 ]; then log "ERROR: Abbruch mit Code $rc"; write_status error "Abbruch mit Code $rc – siehe $LOG_FILE"; fi' EXIT

# Log auf die letzten 2000 Zeilen begrenzen
if [ -f "$LOG_FILE" ] && [ "$(wc -l < "$LOG_FILE")" -gt 2000 ]; then
    tail -n 2000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi

[ "$DEBOUNCE" -gt 0 ] && sleep "$DEBOUNCE"

# Nur ein Lauf gleichzeitig (Timer und Path-Unit können sich überschneiden)
exec 9>"$STATE_DIR/run.lock"
flock -w 300 9 || { log "Anderer Sync-Lauf hält den Lock – übersprungen."; exit 0; }

log "=== $(date '+%Y-%m-%d %H:%M:%S')$([ "$DRY_RUN" = 1 ] && echo ' (dry-run)') ==="
cd "$REPO_DIR"

# --- 1. Pull (rebase + autostash: keine Merge-Commits, lokale Edits in memory/ überleben) ---
if [ "$DRY_RUN" = 0 ]; then
    git pull --quiet --rebase --autostash origin main >> "$LOG_FILE" 2>&1
fi

# --- 2. Claude-Code-Memories spiegeln ---
# ~/.claude/projects/<projekt>/memory/ -> claude-memories/<projekt>/ (führender Bindestrich weg, klein).
# Leere memory/-Ordner und Background-Job-Verzeichnisse werden übersprungen,
# Spiegel von Projekten ohne Memory werden entfernt.
if [ -d "$CC_PROJECTS_DIR" ]; then
    declare -A active=()
    shopt -s nullglob
    for src in "$CC_PROJECTS_DIR"/*/memory; do
        proj="$(basename "$(dirname "$src")")"
        case "$proj" in *-claude-jobs-*) continue ;; esac
        mds=("$src"/*.md)
        [ ${#mds[@]} -eq 0 ] && continue
        name="$(echo "${proj#-}" | tr '[:upper:]' '[:lower:]')"
        active[$name]=1
        if [ "$DRY_RUN" = 1 ]; then
            log "würde spiegeln: $src -> claude-memories/$name/"
        else
            mkdir -p "$MIRROR_DIR/$name"
            rsync -a --delete --include='*/' --include='*.md' --exclude='*' \
                  "$src/" "$MIRROR_DIR/$name/" >> "$LOG_FILE" 2>&1
        fi
    done
    for dir in "$MIRROR_DIR"/*/; do
        name="$(basename "$dir")"
        [ -n "${active[$name]:-}" ] && continue
        if [ "$DRY_RUN" = 1 ]; then
            log "würde entfernen: claude-memories/$name/"
        else
            rm -rf "$dir"
            log "Entfernt (keine Quelle mehr): claude-memories/$name/"
        fi
    done
    shopt -u nullglob
    log "Claude-Memories: ${#active[@]} Projekte."
fi

# --- 3. Hermes: USER.md vom Default in die Profile verteilen, dann alle Profile spiegeln ---
if [ "$DRY_RUN" = 1 ]; then
    "$PY" "$HELPER" --repo "$REPO_DIR" propagate-user --dry-run
else
    "$PY" "$HELPER" --repo "$REPO_DIR" propagate-user >> "$LOG_FILE" 2>&1
    "$PY" "$HELPER" --repo "$REPO_DIR" mirror >> "$LOG_FILE" 2>&1
fi

# Nur vorhandene Ordner an git übergeben (frische Kopie: Spiegel existieren evtl. noch nicht)
SYNC_PATHS=()
for d in memory claude-memories hermes-memories; do [ -d "$d" ] && SYNC_PATHS+=("$d/"); done

# --- 4. Prüfen (Ergebnis erscheint im Dashboard-Tab „Memory“) ---
if [ "$DRY_RUN" = 1 ]; then
    "$PY" "$HELPER" --repo "$REPO_DIR" lint --out "$STATE_DIR/lint.dry-run.json"
    git status --short -- "${SYNC_PATHS[@]}"
    exit 0
fi
"$PY" "$HELPER" --repo "$REPO_DIR" lint --quiet --out "$STATE_DIR/lint.json" >> "$LOG_FILE" 2>&1

# --- 5. Commit + Push ---
if [ -n "$(git status --porcelain -- "${SYNC_PATHS[@]}")" ]; then
    git add -A -- "${SYNC_PATHS[@]}"
    areas="$(git diff --cached --name-only | cut -d/ -f1 | sort -u | paste -sd, -)"
    git commit --quiet -m "memory: auto-sync $(date '+%Y-%m-%d %H:%M') ($areas)" >> "$LOG_FILE" 2>&1
    log "Committet: $areas"
fi
if [ "$(git rev-list --count origin/main..HEAD)" -gt 0 ]; then
    # Offline ist nicht fatal: der Commit bleibt lokal und geht beim nächsten Lauf mit
    if git push --quiet origin HEAD:main >> "$LOG_FILE" 2>&1; then
        log "Gepusht."
        write_status ok "Gepusht"
    else
        log "WARN: git push fehlgeschlagen – nächster Lauf versucht es erneut."
        write_status error "Push fehlgeschlagen, Commit liegt lokal"
    fi
else
    log "Keine Änderungen."
    write_status ok "Keine Änderungen"
fi
echo "" >> "$LOG_FILE"
