#!/bin/bash
# install-hermes-sync.sh – Memory-Sync und Hermes-Dashboard-Tab aus diesem Repo einrichten.
# Idempotent; dieses Repo ist die einzige Quelle für Skript, Units und Plugin.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

mkdir -p "$HOME/.local/bin" "$UNIT_DIR"

ln -sfn "$REPO_DIR/scripts/ai-knowledge-sync.sh" "$HOME/.local/bin/ai-knowledge-sync.sh"
echo "✓ ~/.local/bin/ai-knowledge-sync.sh -> $REPO_DIR/scripts/"

for unit in "$REPO_DIR"/systemd/*; do
    ln -sfn "$unit" "$UNIT_DIR/$(basename "$unit")"
done
echo "✓ Units verlinkt: $(cd "$REPO_DIR/systemd" && echo *)"

# Profile mit eigenem Memory zusätzlich beobachten (maschinenspezifisch -> Drop-in, nicht im Repo)
mkdir -p "$UNIT_DIR/memory-sync.path.d"
{
    echo "# Erzeugt von install-hermes-sync.sh – bei neuen Profilen erneut ausführen"
    echo "[Path]"
    shopt -s nullglob
    for dir in "$HERMES_HOME"/profiles/*/memories; do
        files=("$dir"/*.md)
        [ ${#files[@]} -gt 0 ] && echo "PathChanged=$dir"
    done
} > "$UNIT_DIR/memory-sync.path.d/profiles.conf"
echo "✓ Profile beobachtet: $(grep -c '^PathChanged' "$UNIT_DIR/memory-sync.path.d/profiles.conf")"

systemctl --user daemon-reload
systemctl --user enable --now memory-sync.timer memory-sync.path >/dev/null
echo "✓ memory-sync.timer + memory-sync.path aktiv"

# Dashboard-Tab „Memory“
if [ -d "$HERMES_HOME" ]; then
    mkdir -p "$HERMES_HOME/plugins"
    ln -sfn "$REPO_DIR/hermes-plugin/wissensablage" "$HERMES_HOME/plugins/wissensablage"
    if command -v hermes >/dev/null; then
        hermes plugins enable wissensablage >/dev/null 2>&1 || true
    fi
    echo "✓ Hermes-Plugin wissensablage verlinkt – Dashboard neu laden (Tab „Memory“)"
fi
