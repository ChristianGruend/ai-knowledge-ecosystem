"""Lossless exact deduplication. Semantic similarity never authorizes deletion."""


def deduplicate(entries):
    return _deduplicate_simple(entries)


def _deduplicate_simple(entries):
    unique = {}
    for entry in entries:
        # Preserve case, whitespace and the complete text: code and paths matter.
        fingerprint = entry['content']
        if fingerprint not in unique:
            unique[fingerprint] = dict(entry)
        else:
            kept = unique[fingerprint]
            sources = set(kept.get('sources', [kept.get('source', 'unknown')]))
            sources.update(entry.get('sources', [entry.get('source', 'unknown')]))
            kept['sources'] = sorted(sources)
    print(f'  Exakte Duplikate entfernt: {len(entries) - len(unique)}')
    return list(unique.values())
