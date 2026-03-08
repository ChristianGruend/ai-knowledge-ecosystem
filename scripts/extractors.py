"""
extractors.py
Zieht Rohdaten aus den Export-Dateien der verschiedenen AI-Systeme.
"""

import json
from pathlib import Path
from bs4 import BeautifulSoup


def extract_claude(export_path: str) -> list[dict]:
    """
    Verarbeitet Claude-Datenexport (JSON).
    Export: claude.ai → Einstellungen → Daten exportieren
    """
    path = Path(export_path)
    if not path.exists():
        print(f"  ⚠️  Claude-Export nicht gefunden: {export_path}")
        return []

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    items = []

    # Memories
    for mem in data.get("memories", []):
        items.append({
            "source": "claude",
            "type": "memory",
            "content": mem.get("content", "").strip(),
            "created": mem.get("created_at", ""),
        })

    # Conversation-Highlights (nur Nachrichten, keine System-Prompts)
    for convo in data.get("conversations", []):
        for msg in convo.get("messages", []):
            if msg.get("role") == "assistant" and len(msg.get("content", "")) > 100:
                items.append({
                    "source": "claude",
                    "type": "conversation_highlight",
                    "content": msg["content"][:500].strip(),
                    "created": convo.get("created_at", ""),
                })

    print(f"  ✅ Claude: {len(items)} Einträge extrahiert")
    return items


def extract_chatgpt(export_path: str) -> list[dict]:
    """
    Verarbeitet ChatGPT-Datenexport (JSON).
    Export: chatgpt.com → Einstellungen → Daten exportieren → memories.json
    """
    path = Path(export_path)
    if not path.exists():
        print(f"  ⚠️  ChatGPT-Export nicht gefunden: {export_path}")
        return []

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    items = []

    # Memories (Liste von Objekten mit "memory"-Feld)
    memory_list = data if isinstance(data, list) else data.get("memories", [])
    for mem in memory_list:
        content = mem.get("memory") or mem.get("content") or ""
        if content.strip():
            items.append({
                "source": "chatgpt",
                "type": "memory",
                "content": content.strip(),
                "created": mem.get("created_at", ""),
            })

    print(f"  ✅ ChatGPT: {len(items)} Einträge extrahiert")
    return items


def extract_gemini(export_path: str) -> list[dict]:
    """
    Verarbeitet Google Takeout → Gemini Apps (HTML).
    Export: takeout.google.com → Gemini Apps auswählen
    """
    path = Path(export_path)
    if not path.exists():
        print(f"  ⚠️  Gemini-Export nicht gefunden: {export_path}")
        return []

    with open(path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    items = []
    for entry in soup.find_all("div", class_="outer-cell"):
        text = entry.get_text(separator="\n").strip()
        if len(text) > 50:
            items.append({
                "source": "gemini",
                "type": "conversation_highlight",
                "content": text[:500].strip(),
                "created": "",
            })

    print(f"  ✅ Gemini: {len(items)} Einträge extrahiert")
    return items


def extract_mistral(export_path: str) -> list[dict]:
    """
    Verarbeitet Mistral-Datenexport (JSON).
    Export: chat.mistral.ai > Einstellungen > Daten exportieren
    """
    path = Path(export_path)
    if not path.exists():
        print(f"  ⚠️  Mistral-Export nicht gefunden: {export_path}")
        return []

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    items = []

    memory_list = data if isinstance(data, list) else data.get("memories", data.get("conversations", []))
    for mem in memory_list:
        content = mem.get("content") or mem.get("memory") or ""
        if content.strip():
            items.append({
                "source": "mistral",
                "type": "memory",
                "content": content.strip(),
                "created": mem.get("created_at", ""),
            })

    print(f"  ✅ Mistral: {len(items)} Einträge extrahiert")
    return items


def extract_copilot(export_path: str) -> list[dict]:
    """
    Verarbeitet Microsoft Copilot-Datenexport (JSON).
    Export: account.microsoft.com > Datenschutz > Aktivitaetsverlauf herunterladen
    """
    path = Path(export_path)
    if not path.exists():
        print(f"  ⚠️  Copilot-Export nicht gefunden: {export_path}")
        return []

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    items = []

    memory_list = data if isinstance(data, list) else data.get("memories", data.get("conversations", []))
    for mem in memory_list:
        content = mem.get("content") or mem.get("memory") or mem.get("text") or ""
        if content.strip():
            items.append({
                "source": "copilot",
                "type": "memory",
                "content": content.strip(),
                "created": mem.get("created_at", mem.get("timestamp", "")),
            })

    print(f"  ✅ Copilot: {len(items)} Einträge extrahiert")
    return items


def extract_manual(manual_dir: str = "exports/manual") -> list[dict]:
    """
    Liest manuelle .md-Einträge aus einem Ordner.
    Nützlich für eigene Notizen, Dokumente, etc.
    """
    path = Path(manual_dir)
    if not path.exists():
        return []

    items = []
    for md_file in path.glob("*.md"):
        content = md_file.read_text(encoding="utf-8").strip()
        if content:
            items.append({
                "source": "manual",
                "type": "note",
                "content": content,
                "created": "",
            })

    if items:
        print(f"  ✅ Manuell: {len(items)} Einträge geladen")
    return items
