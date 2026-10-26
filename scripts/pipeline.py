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
    # Relative paths belong to the configuration file, not the caller's cwd.
    config_root = Path(config_path).resolve().parent
    def resolve(value):
        path = Path(value)
        return str(path if path.is_absolute() else config_root / path)

    exports = {name: resolve(path) for name, path in config.get("exports", {}).items() if path}
    config["output_dir"] = resolve(config.get("output_dir", "knowledge-base"))
    config["prompts_dir"] = resolve(config.get("prompts_dir", "prompts"))
    config["memory_files"] = [resolve(path) for path in config.get("memory_files", [])]
    for path in config["memory_files"]:
        if not Path(path).is_file():
            raise FileNotFoundError(f"Konfigurierte Memory-Datei fehlt: {path}")

    # ── SCHRITT 1: Extraktion ──────────────────────
    print("\n📥 Schritt 1: Extraktion")
    raw = []
    raw += extract_claude(exports.get("claude", ""))
    raw += extract_chatgpt(exports.get("chatgpt", ""))
    raw += extract_gemini(exports.get("gemini", ""))
    raw += extract_mistral(exports.get("mistral", ""))
    raw += extract_copilot(exports.get("copilot", ""))
    raw += extract_manual(resolve(config.get("manual_dir", "exports/manual")))

    if not raw:
        print("\nKeine Exports gefunden; nutze vorhandenes Wissen und konfigurierte Memories.")
        generate_all_prompts(config["output_dir"], config["prompts_dir"], config)
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
    import argparse
    parser = argparse.ArgumentParser(description="Exporte normalisieren und System-Prompts erzeugen.")
    parser.add_argument("config", nargs="?", default="config.json", help="Pfad zur Config (Standard: config.json)")
    run(parser.parse_args().config)
