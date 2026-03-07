"""
normalize.py
Vereinheitlicht alle Rohdaten in strukturierte .md-Dateien.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path


def load_config(config_path: str = "config.json") -> dict:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def categorize(content: str, categories: dict) -> str:
    content_lower = content.lower()
    for category, keywords in categories.items():
        if any(kw in content_lower for kw in keywords):
            return category
    return "general"


def to_markdown(entry: dict) -> str:
    return f"""---
id: {entry['id']}
source: {entry['source']}
type: {entry['type']}
category: {entry['category']}
created: {entry['created'] or datetime.now().isoformat()}
updated: {entry['updated']}
---

{entry['content']}
"""


def normalize_all(raw_items: list[dict], config: dict) -> list[dict]:
    categories = config.get("categories", {})
    normalized = []

    for item in raw_items:
        content = item.get("content", "").strip()
        if not content or len(content) < 10:
            continue

        normalized.append({
            "id": str(uuid.uuid4()),
            "source": item.get("source", "unknown"),
            "type": item.get("type", "fact"),
            "category": categorize(content, categories),
            "content": content,
            "created": item.get("created", ""),
            "updated": datetime.now().isoformat(),
        })

    return normalized


def save_to_disk(entries: list[dict], output_dir: str):
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)

    # Alte Einträge löschen (vollständige Neugenerierung)
    for old_file in base.rglob("*.md"):
        old_file.unlink()

    for entry in entries:
        cat_dir = base / entry["category"]
        cat_dir.mkdir(exist_ok=True)
        filename = f"{entry['id'][:8]}_{entry['source']}.md"
        (cat_dir / filename).write_text(to_markdown(entry), encoding="utf-8")

    print(f"  💾 {len(entries)} Einträge gespeichert in '{output_dir}/'")
