#!/usr/bin/env bash
# Installiert alle verfügbaren Claude Code Plugins mit Skills/Commands
# Ausführen in einem NEUEN Terminal (nicht innerhalb einer Claude-Session):
#   bash ~/install-all-plugins.sh

set -e

PLUGINS=(
  "frontend-design"        # Skill: frontend-design (hochwertige UI/UX-Implementierung)
  "playground"             # Skill: playground (interaktive HTML-Explorers)
  "plugin-dev"             # Skills: skill/command/agent/hook/mcp/plugin-structure-development
  "claude-code-setup"      # Skill: claude-automation-recommender
  "skill-creator"          # Skill: skill-creator (Skills erstellen + optimieren)
  "hookify"                # Skill: writing-hookify-rules + Hook-Verwaltung
  "math-olympiad"          # Skill: math-olympiad (Olympiade-Matheaufgaben)
  "claude-md-management"   # Skill: claude-md-improver (CLAUDE.md Audit)
  "mcp-server-dev"         # Skills: build-mcp-server, build-mcp-app, build-mcpb
  "pr-review-toolkit"      # Command: /review-pr
  "commit-commands"        # Commands: /commit, /commit-push-pr, /clean_gone
  "feature-dev"            # Command: /feature-dev (Agent-basierte Feature-Entwicklung)
  "ralph-loop"             # Command: /ralph-loop (Loop-Automatisierung)
  "code-simplifier"        # Agent: code-simplifier
  "agent-sdk-dev"          # Commands + Agents für Claude Agent SDK
  "security-guidance"      # Hook: Security-Hinweise bei sensiblen Operationen
)

echo "Installiere ${#PLUGINS[@]} Plugins..."
echo ""

for plugin in "${PLUGINS[@]}"; do
  echo "→ claude plugin install $plugin"
  claude plugin install "$plugin" --yes 2>&1 || echo "  ⚠ Fehler bei $plugin (wird übersprungen)"
  echo ""
done

echo "✓ Fertig! Neue Claude-Session starten, um alle Skills zu aktivieren."
