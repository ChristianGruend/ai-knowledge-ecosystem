"""Deterministic normalization and non-destructive import storage."""
import hashlib
import json
import re
from pathlib import Path
from scripts.storage import write_if_changed


def load_config(config_path='config.json'):
    with open(config_path, encoding='utf-8') as handle:
        return json.load(handle)


def categorize(content, categories):
    for category, keywords in categories.items():
        if any(re.search(r'(?<!\w)' + re.escape(kw) + r'(?!\w)', content, re.I)
               for kw in keywords if kw):
            return category
    return 'general'


def to_markdown(entry):
    # JSON scalars/arrays are valid YAML and safely escape imported metadata.
    keys = ('id', 'source', 'sources', 'type', 'category', 'created', 'updated')
    frontmatter = '\n'.join(f'{key}: {json.dumps(entry.get(key, ""), ensure_ascii=False)}' for key in keys)
    return f'---\n{frontmatter}\n---\n\n{entry["content"]}\n'


def normalize_all(raw_items, config):
    normalized = []
    for item in raw_items:
        content = item.get('content', '').strip()
        if len(content) < 10:
            continue
        if any(keyword.casefold() in content.casefold() for keyword in config.get('exclude_keywords', []) if keyword):
            continue
        source = item.get('source', 'unknown')
        normalized.append({
            'id': hashlib.sha256(content.encode('utf-8')).hexdigest(),
            'source': source,
            'sources': item.get('sources', [source]),
            'type': item.get('type', 'fact'),
            'category': categorize(content, config.get('categories', {})),
            'content': content,
            'created': item.get('created', ''),
            'updated': item.get('updated', item.get('created', '')),
        })
    return normalized


def save_to_disk(entries, output_dir):
    # Never delete existing notes, including imports absent from a partial export.
    base = Path(output_dir) / '_imports'
    base.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        # Derive the filename here as well: imported metadata cannot escape base.
        digest = hashlib.sha256(entry['content'].encode('utf-8')).hexdigest()
        target = base / f'{digest}.md'
        if target.exists():
            continue  # First imported record stays intact; imports are append-only.
        write_if_changed(target, to_markdown(entry))
    print(f'  Imports sicher gespeichert: {base}')
