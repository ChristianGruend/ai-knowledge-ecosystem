"""
deduplicate.py
Erkennt und entfernt semantische Duplikate via Claude API.
Fällt ohne API-Key auf einfache Textvergleiche zurück.
"""

import json
import os


def deduplicate(entries: list[dict]) -> list[dict]:
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key:
        return _deduplicate_ai(entries, api_key)
    else:
        print("  ℹ️  Kein ANTHROPIC_API_KEY – nutze einfache Deduplizierung")
        return _deduplicate_simple(entries)


def _deduplicate_simple(entries: list[dict]) -> list[dict]:
    """Entfernt exakte und sehr ähnliche Duplikate ohne API."""
    seen = set()
    unique = []

    for entry in entries:
        # Normalisierter Fingerprint
        fingerprint = " ".join(entry["content"].lower().split())[:200]
        if fingerprint not in seen:
            seen.add(fingerprint)
            unique.append(entry)

    removed = len(entries) - len(unique)
    print(f"  🧹 Einfache Deduplizierung: {removed} Duplikate entfernt")
    return unique


def _deduplicate_ai(entries: list[dict], api_key: str) -> list[dict]:
    """Nutzt Claude API für semantische Duplikatserkennung."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    # In Batches aufteilen (max 50 pro Aufruf)
    batch_size = 50
    to_remove = set()

    for i in range(0, len(entries), batch_size):
        batch = entries[i:i + batch_size]
        contents = [e["content"][:300] for e in batch]

        try:
            response = client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": (
                        "Analysiere diese Wissenseinträge und identifiziere semantische Duplikate "
                        "(gleicher Inhalt, nur anders formuliert). "
                        "Antworte NUR mit JSON, kein Text davor oder danach.\n"
                        "Format: {\"duplicates\": [[0,3], [1,5]]}\n\n"
                        f"Einträge:\n{json.dumps(contents, ensure_ascii=False, indent=2)}"
                    )
                }]
            )

            raw = response.content[0].text.strip()
            result = json.loads(raw)

            for group in result.get("duplicates", []):
                for idx in group[1:]:
                    to_remove.add(i + idx)

        except Exception as e:
            print(f"  ⚠️  AI-Deduplizierung fehlgeschlagen (Batch {i}): {e}")

    unique = [e for idx, e in enumerate(entries) if idx not in to_remove]
    removed = len(entries) - len(unique)
    print(f"  🧹 KI-Deduplizierung: {removed} Duplikate entfernt")
    return unique
