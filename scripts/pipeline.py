"""
pipeline.py
Haupt-Pipeline: Extraktion → Normalisierung → Deduplizierung → Speichern → Prompts generieren
"""

import json
import sys
from pathlib import Path

# Ensure package imports work when running the file directly.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.extractors import (
    extract_claude,
    extract_chatgpt,
    extract_gemini,
    extract_mistral,
    extract_copilot,
    extract_manual,
)
from scripts.normalize import normalize_all, save_to_disk, load_config
from scripts.deduplicate import deduplicate
from scripts.injectors import generate_all_prompts


def run(config_path: str = "config.json"):
    print("\n🚀 AI Knowledge Ecosystem Pipeline")
    print("=" * 45)

    # Config laden
    config = load_config(config_path)
    exports = config.get("exports", {})

    # ── SCHRITT 1: Extraktion ──────────────────────
    print("\n📥 Schritt 1: Extraktion")
    raw = []
    raw += extract_claude(exports.get("claude", ""))
    raw += extract_chatgpt(exports.get("chatgpt", ""))
    raw += extract_gemini(exports.get("gemini", ""))
    raw += extract_mistral(exports.get("mistral", ""))
    raw += extract_copilot(exports.get("copilot", ""))
    raw += extract_manual()

    if not raw:
        print("\n⚠️  Keine Daten gefunden. Bitte Exports in 'exports/' ablegen.")
        print("   Siehe README.md für Anleitung.")
        return

    print(f"   Gesamt: {len(raw)} Rohdaten")

    # ── SCHRITT 2: Normalisierung ──────────────────
    print("\n📐 Schritt 2: Normalisierung")
    normalized = normalize_all(raw, config)
    print(f"   {len(normalized)} Einträge normalisiert")

    # ── SCHRITT 3: Deduplizierung ──────────────────
    print("\n🧹 Schritt 3: Deduplizierung")
    if config.get("deduplicate", True):
        unique = deduplicate(normalized)
    else:
        unique = normalized
        print("   (übersprungen – in config.json deaktiviert)")

    # ── SCHRITT 4: Speichern ───────────────────────
    print("\n💾 Schritt 4: Wissensbasis speichern")
    save_to_disk(unique, config["output_dir"])

    # ── SCHRITT 5: Prompts generieren ─────────────
    print("\n📝 Schritt 5: AI-Prompts generieren")
    generate_all_prompts(config["output_dir"], config.get("prompts_dir", "prompts"), config)

    # ── FERTIG ─────────────────────────────────────
    print("\n" + "=" * 45)
    print(f"✨ Pipeline abgeschlossen!")
    print(f"   📊 Einträge: {len(unique)}")
    print(f"   📁 Wissensbasis: {config['output_dir']}/")
    print(f"   📝 Prompts: {config.get('prompts_dir', 'prompts')}/")
    print("\nNächster Schritt: Prompts in deine AIs einspeisen")
    print("  → claude_project.md    in Claude Projects")
    print("  → chatgpt_custom_gpt.md in Custom GPT Instructions")
    print("  → gemini_gem.md        in Gemini Gems")
    print("  → mistral_agent.md     in Mistral Agents")
    print("  → copilot_gpt.md       in Microsoft Copilot GPTs")


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    run(config_path)
