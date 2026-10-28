"""Hermes-Plugin wissensablage: /memory-sync für TUI, CLI und Messaging.

Der Dashboard-Tab liegt unter dashboard/. Sync und Prüfung selbst leben in
ai-knowledge-data (scripts/ai-knowledge-sync.sh, scripts/hermes_memory.py).
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

STATE = Path(os.environ.get("AI_KNOWLEDGE_STATE_DIR",
                            Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
                            / "ai-knowledge-sync"))

_HELP = """/memory-sync          Sync jetzt anstoßen (läuft im Hintergrund über systemd)
/memory-sync status   letzter Sync und Prüfbefunde
/memory-sync help     diese Hilfe"""


def _read(name: str):
    try:
        return json.loads((STATE / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _status() -> str:
    sync, lint = _read("status.json") or {}, _read("lint.json")
    lines = [f"Letzter Sync: {sync.get('result', 'unbekannt')} · {sync.get('finished_at', '–')} · {sync.get('message', '')}"]
    if lint:
        c = lint["counts"]
        lines.append(f"Prüfung {lint['generated_at']}: {c['error']} Fehler, {c['warn']} Warnungen, {c['info']} Hinweise")
        lines += [f"  [{f['level']}] {f['file']} – {f['message']}" for f in lint["findings"] if f["level"] != "info"]
    lines.append("Details: Dashboard → Tab „Memory“")
    return "\n".join(lines)


def _handle(raw_args: str) -> Optional[str]:
    arg = raw_args.strip().split()[0] if raw_args.strip() else ""
    if arg in {"help", "-h", "--help"}:
        return _HELP
    if arg == "status":
        return _status()
    if arg:
        return f"Unbekannt: {arg}\n\n{_HELP}"
    done = subprocess.run(["systemctl", "--user", "start", "--no-block", "memory-sync.service"],
                          capture_output=True, text=True, timeout=15)
    if done.returncode != 0:
        return f"Sync nicht gestartet: {done.stderr.strip()}"
    return "Sync gestartet (Pull, Profile angleichen, prüfen, Push). Ergebnis: /memory-sync status"


def register(ctx) -> None:
    ctx.register_command("memory-sync", handler=_handle,
                         description="Memories mit ai-knowledge-data synchronisieren und prüfen.")
