"""Backend des Dashboard-Tabs „Memory“, gemountet unter /api/plugins/wissensablage/.

Liest den Zustand, den ai-knowledge-sync.sh und scripts/hermes_memory.py schreiben
(~/.local/state/ai-knowledge-sync/{status,lint}.json), und stößt Sync bzw. Prüfung an.
Die Memory-Dateien selbst werden hier nur gelesen – geschrieben wird ausschließlich über
Hermes' Memory-Tool oder den Sync, beide mit Hermes' eigenem Datei-Lock.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

REPO = Path(os.environ.get("AI_KNOWLEDGE_DATA_DIR", Path.home() / "Projekte" / "ai-knowledge-data"))
STATE = Path(os.environ.get("AI_KNOWLEDGE_STATE_DIR",
                            Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
                            / "ai-knowledge-sync"))
LOG = Path.home() / ".local" / "share" / "ai-knowledge-sync.log"
HELPER = REPO / "scripts" / "hermes_memory.py"


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _systemctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True, timeout=15)


def _unit_state() -> dict:
    out = {}
    try:
        show = _systemctl("show", "memory-sync.service", "memory-sync.timer", "memory-sync.path",
                          "--property=Id,ActiveState,NextElapseUSecRealtime,LastTriggerUSec").stdout
    except (OSError, subprocess.SubprocessError):
        return out
    for block in show.strip().split("\n\n"):
        props = dict(line.split("=", 1) for line in block.splitlines() if "=" in line)
        if props.get("Id"):
            out[props["Id"]] = props
    return out


@router.get("/status")
async def status():
    try:
        log_tail = LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
    except OSError:
        log_tail = []
    return {
        "sync": _read_json(STATE / "status.json"),
        "lint": _read_json(STATE / "lint.json"),
        "units": _unit_state(),
        "log_tail": log_tail,
        "repo": str(REPO),
    }


@router.post("/sync")
async def sync():
    result = _systemctl("start", "--no-block", "memory-sync.service")
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr.strip() or "systemctl fehlgeschlagen")
    return {"started": True}


@router.post("/lint")
async def lint():
    if not HELPER.exists():
        raise HTTPException(status_code=500, detail=f"{HELPER} fehlt")
    result = subprocess.run([sys.executable, str(HELPER), "--repo", str(REPO), "lint", "--quiet",
                             "--out", str(STATE / "lint.json")], capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr.strip()[-500:])
    return _read_json(STATE / "lint.json")
