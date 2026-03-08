"""
injectors.py
Generiert System-Prompts aus der Wissensdatenbank für jede AI-Plattform.
"""

import json
from pathlib import Path
from datetime import datetime


def load_knowledge(knowledge_dir: str) -> str:
    """Liest alle .md-Dateien und gibt sie zusammengefügt zurück."""
    base = Path(knowledge_dir)
    sections = []

    for cat_dir in sorted(base.iterdir()):
        if not cat_dir.is_dir():
            continue

        entries = []
        for md_file in sorted(cat_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            # YAML Frontmatter entfernen
            lines = content.split("\n")
            try:
                second_dash = lines.index("---", 1)
                body = "\n".join(lines[second_dash + 1:]).strip()
            except ValueError:
                body = content.strip()
            if body:
                entries.append(body)

        if entries:
            sections.append(f"## {cat_dir.name.upper()}\n\n" + "\n\n---\n\n".join(entries))

    updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"# WISSENSDATENBANK\n_Zuletzt aktualisiert: {updated}_\n\n"
    return header + "\n\n".join(sections)


def generate_all_prompts(knowledge_dir: str, prompts_dir: str, config: dict):
    """Generiert und speichert System-Prompts für alle AI-Systeme."""
    knowledge = load_knowledge(knowledge_dir)
    limits = config.get("max_prompt_chars", {})
    Path(prompts_dir).mkdir(exist_ok=True)

    # --- Claude (kein Zeichenlimit in der Praxis) ---
    claude_prompt = _wrap_claude(knowledge)
    _save_prompt(prompts_dir, "claude_project.md", claude_prompt, limits.get("claude", 200000))

    # --- ChatGPT Custom GPT (ca. 8.000 Zeichen) ---
    chatgpt_prompt = _wrap_chatgpt(knowledge)
    _save_prompt(prompts_dir, "chatgpt_custom_gpt.md", chatgpt_prompt, limits.get("chatgpt", 8000))

    # --- Gemini Gem ---
    gemini_prompt = _wrap_gemini(knowledge)
    _save_prompt(prompts_dir, "gemini_gem.md", gemini_prompt, limits.get("gemini", 50000))

    # --- Mistral Agent ---
    mistral_prompt = _wrap_mistral(knowledge)
    _save_prompt(prompts_dir, "mistral_agent.md", mistral_prompt, limits.get("mistral", 32000))

    # --- Microsoft Copilot GPT ---
    copilot_prompt = _wrap_copilot(knowledge)
    _save_prompt(prompts_dir, "copilot_gpt.md", copilot_prompt, limits.get("copilot", 32000))

    print(f"  📝 Prompts gespeichert in '{prompts_dir}/'")


def _wrap_claude(knowledge: str) -> str:
    return f"""Du hast Zugriff auf eine persönliche Wissensdatenbank des Nutzers.
Nutze dieses Wissen, um präzisere, persönlichere Antworten zu geben.

{knowledge}
"""


def _wrap_chatgpt(knowledge: str) -> str:
    return f"""You have access to the user's personal knowledge base.
Use this information to give more accurate, personalized answers.
Always refer to this knowledge when relevant.

{knowledge}
"""


def _wrap_gemini(knowledge: str) -> str:
    return f"""Du bist ein persönlicher KI-Assistent mit Zugriff auf die Wissensdatenbank des Nutzers.
Beziehe dieses Wissen in alle relevanten Antworten ein.

{knowledge}
"""


def _wrap_mistral(knowledge: str) -> str:
    return f"""Du bist ein persoenlicher KI-Assistent mit Zugriff auf die Wissensdatenbank des Nutzers.
Nutze dieses Wissen fuer praezisere und persoenlichere Antworten.

{knowledge}
"""


def _wrap_copilot(knowledge: str) -> str:
    return f"""You are a personal AI assistant with access to the user's knowledge base.
Use this knowledge for more precise and personalized answers.

{knowledge}
"""


def _save_prompt(prompts_dir: str, filename: str, content: str, max_chars: int):
    filepath = Path(prompts_dir) / filename

    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n_[Wissensbasis gekürzt – Zeichenlimit erreicht]_"
        print(f"  ⚠️  {filename}: auf {max_chars} Zeichen gekürzt")

    filepath.write_text(content, encoding="utf-8")
    print(f"     → {filename} ({len(content):,} Zeichen)")
