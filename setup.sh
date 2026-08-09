#!/bin/bash
# setup.sh — Einmalig auf jedem System ausführen
# Erstellt Symlink: ~/.claude/CLAUDE.md → <repo>/memory/CLAUDE.md

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
TARGET="$REPO_DIR/memory/CLAUDE.md"
LINK="$CLAUDE_DIR/CLAUDE.md"

mkdir -p "$CLAUDE_DIR"

if [ -L "$LINK" ]; then
    echo "Symlink existiert bereits: $LINK → $(readlink "$LINK")"
elif [ -f "$LINK" ]; then
    echo "WARNUNG: $LINK ist eine normale Datei (kein Symlink)."
    echo "Backup: ${LINK}.bak"
    mv "$LINK" "${LINK}.bak"
    ln -s "$TARGET" "$LINK"
    echo "Symlink erstellt: $LINK → $TARGET"
else
    ln -s "$TARGET" "$LINK"
    echo "Symlink erstellt: $LINK → $TARGET"
fi
