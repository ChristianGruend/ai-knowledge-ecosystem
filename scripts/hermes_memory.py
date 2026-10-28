#!/usr/bin/env python3
"""Hermes-Memories mit ai-knowledge-data abgleichen und alle Memories prüfen.

Unterbefehle (vom Sync-Skript und vom Hermes-Dashboard-Plugin genutzt):

  mirror          Default- und Profil-Memories nach <repo>/hermes-memories/ spiegeln
  propagate-user  USER.md des Default-Profils in alle Profile mit eigenem Memory verteilen
  lint            Hermes-, Quell- und Claude-Memories prüfen, Befunde nach status.json schreiben

Schreibzugriffe auf ~/.hermes/**/memories/*.md laufen wie in Hermes selbst
(tools/memory_tool_store.py): exklusiver flock auf <datei>.lock, dann Temp-Datei
+ atomares rename. Hermes liest bei jedem Memory-Write unter demselben Lock neu ein,
dadurch gibt es keine verlorenen Updates.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

ENTRY_DELIMITER = "\n§\n"
DEFAULT_LIMITS = {"MEMORY.md": 2200, "USER.md": 1375}
LIMIT_KEYS = {"MEMORY.md": "memory_char_limit", "USER.md": "user_char_limit"}

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
CLAUDE_PROJECTS = Path(os.environ.get("CLAUDE_PROJECTS_DIR", Path.home() / ".claude" / "projects"))
STATE_DIR = Path(os.environ.get("AI_KNOWLEDGE_STATE_DIR",
                                Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
                                / "ai-knowledge-sync"))

# Stand-Kopf: höchstens so viele Tage alt, sonst Warnung
STAND_MAX_DAYS = {"CURRENT_CONTEXT.md": 31}
STAND_MAX_DAYS_DEFAULT = 120
MONTHS = {m: i for i, m in enumerate(
    ["januar", "februar", "märz", "april", "mai", "juni", "juli", "august",
     "september", "oktober", "november", "dezember"], start=1)}
MONTHS["maerz"] = 3
PATH_RE = re.compile(r"(?<![\w/.~-])((?:~|/home/[\w.-]+)/[\w./-]*[\w/])")


# ---------------------------------------------------------------- Hermes-Dateien

def profiles() -> dict[str, Path]:
    """Name -> HERMES_HOME aller Profile, ``default`` zuerst."""
    homes = {"default": HERMES_HOME}
    root = HERMES_HOME / "profiles"
    if root.is_dir():
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / "config.yaml").exists():
                homes[child.name] = child
    return homes


def _memory_config(home: Path) -> dict:
    cfg_file = home / "config.yaml"
    if not cfg_file.exists():
        return {}
    text = cfg_file.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:  # ohne PyYAML: flache Schlüssel des memory:-Blocks selbst lesen
        return _memory_block_fallback(text)
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return {}
    mem = data.get("memory") if isinstance(data, dict) else None
    return mem if isinstance(mem, dict) else {}


def _memory_block_fallback(text: str) -> dict:
    block, inside = {}, False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            inside = line.split("#")[0].strip() == "memory:"
            continue
        if inside and (m := re.match(r"\s+(\w+):\s*([^#]*)", line)):
            value = m[2].strip().strip("'\"")
            low = value.lower()
            block[m[1]] = (True if low == "true" else False if low == "false"
                           else int(value) if value.isdigit() else value)
    return block


def memory_enabled(home: Path) -> bool:
    cfg = _memory_config(home)
    return cfg.get("memory_enabled", True) is not False or cfg.get("user_profile_enabled", True) is not False


def char_limit(home: Path, name: str) -> int:
    value = _memory_config(home).get(LIMIT_KEYS[name])
    return value if isinstance(value, int) and value > 0 else DEFAULT_LIMITS[name]


def parse_entries(raw: str) -> list[str]:
    return [e.strip() for e in raw.split(ENTRY_DELIMITER) if e.strip()]


def render_entries(entries: list[str]) -> str:
    return ENTRY_DELIMITER.join(entries)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@contextmanager
def hermes_lock(path: Path):
    """Derselbe Lock wie Hermes: flock auf ``<datei>.lock`` neben der Datei."""
    lock_path = path.with_name(path.name + ".lock")
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def atomic_write(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------- mirror

def cmd_mirror(repo: Path) -> list[str]:
    """Spiegelt default -> hermes-memories/default/, Profile -> hermes-memories/profiles/<name>/."""
    target_root = repo / "hermes-memories"
    wanted: dict[Path, Path] = {}
    for name, home in profiles().items():
        src_dir = home / "memories"
        files = sorted(src_dir.glob("*.md")) if src_dir.is_dir() else []
        if not files:
            continue
        dest_dir = target_root / "default" if name == "default" else target_root / "profiles" / name
        for f in files:
            wanted[dest_dir / f.name] = f

    changed = []
    for dest, src in wanted.items():
        data = src.read_bytes()
        if not dest.exists() or dest.read_bytes() != data:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            changed.append(str(dest.relative_to(repo)))
    # Verwaiste Spiegeldateien entfernen (auch das alte flache Layout hermes-memories/*.md)
    if target_root.is_dir():
        for existing in sorted(target_root.rglob("*.md")):
            if existing not in wanted:
                existing.unlink()
                changed.append(f"-{existing.relative_to(repo)}")
        for d in sorted((p for p in target_root.rglob("*") if p.is_dir()), reverse=True):
            if not any(d.iterdir()):
                d.rmdir()
    return changed


# ---------------------------------------------------------------- propagate-user

def _load_state() -> dict:
    try:
        return json.loads((STATE_DIR / "propagation.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write(STATE_DIR / "propagation.json", json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def cmd_propagate_user(dry_run: bool = False) -> list[dict]:
    """Default-USER.md ist die Quelle. Profile mit aktivem Memory bekommen eine Kopie.

    Hat ein Profil seine Kopie seit der letzten Verteilung selbst geändert, wird die alte
    Fassung vorher gesichert und ihre zusätzlichen Einträge werden gemeldet, damit nichts
    stillschweigend verloren geht.
    """
    src = HERMES_HOME / "memories" / "USER.md"
    if not src.exists():
        return []
    with hermes_lock(src):
        source_text = src.read_text(encoding="utf-8")
    source_entries = parse_entries(source_text)
    state = _load_state()
    results = []
    for name, home in profiles().items():
        if name == "default" or not memory_enabled(home):
            continue
        dest = home / "memories" / "USER.md"
        if not dest.exists():  # nur Profile, die bewusst ein Nutzerprofil führen
            continue
        with hermes_lock(dest):
            current = dest.read_text(encoding="utf-8") if dest.exists() else ""
            if parse_entries(current) == source_entries:
                state[name] = sha(source_text)
                continue
            info = {"profile": name, "action": "updated", "backup": None, "extra_entries": []}
            local_edit = bool(current.strip()) and state.get(name) != sha(current)
            if local_edit:
                info["extra_entries"] = [e for e in parse_entries(current) if e not in source_entries]
                if not dry_run and info["extra_entries"]:
                    backup_dir = STATE_DIR / "backups"
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    backup = backup_dir / f"{name}-USER-{time.strftime('%Y%m%d-%H%M%S')}.md"
                    backup.write_text(current, encoding="utf-8")
                    info["backup"] = str(backup)
            if not dry_run:
                atomic_write(dest, source_text)
                state[name] = sha(source_text)
            else:
                info["action"] = "would-update"
            results.append(info)
    if not dry_run:
        _save_state(state)
    return results


# ---------------------------------------------------------------- lint

def _finding(level: str, area: str, file: str, message: str) -> dict:
    return {"level": level, "area": area, "file": file, "message": message}


def _git_last_change(repo: Path, rel: str) -> date | None:
    try:
        out = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%cs", "--", rel],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return date.fromisoformat(out) if out else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def parse_stand(text: str) -> date | None:
    """``<!-- Stand: Juli 2026 -->``, ``Stand: 2026-10-12`` oder ``Stand: 12.10.2026``."""
    m = re.search(r"Stand:\s*([^\n>-][^\n>]*?)\s*(?:-->|$)", "\n".join(text.splitlines()[:8]), re.M)
    if not m:
        return None
    value = m.group(1).strip().lower()
    if iso := re.search(r"(\d{4})-(\d{2})-(\d{2})", value):
        return date(int(iso[1]), int(iso[2]), int(iso[3]))
    if de := re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", value):
        return date(int(de[3]), int(de[2]), int(de[1]))
    if mon := re.search(r"([a-zäöü]+)\s+(\d{4})", value):
        if mon[1] in MONTHS:
            return date(int(mon[2]), MONTHS[mon[1]], 1)
    return None


def _months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + b.month - a.month


def lint_hermes() -> tuple[list[dict], list[dict]]:
    findings, overview = [], []
    default_user = HERMES_HOME / "memories" / "USER.md"
    default_user_entries = parse_entries(default_user.read_text(encoding="utf-8")) if default_user.exists() else []
    for name, home in profiles().items():
        enabled = memory_enabled(home)
        for fname in ("MEMORY.md", "USER.md"):
            path = home / "memories" / fname
            label = f"{name}/{fname}"
            if not path.exists():
                continue
            raw = path.read_text(encoding="utf-8")
            entries = parse_entries(raw)
            limit = char_limit(home, fname)
            used = len(render_entries(entries))
            overview.append({"profile": name, "file": fname, "enabled": enabled, "entries": entries,
                             "chars": used, "limit": limit, "path": str(path)})
            if used > limit:
                findings.append(_finding("error", "hermes", label, f"{used}/{limit} Zeichen – über dem Limit, Hermes verweigert neue Einträge"))
            elif used > 0.85 * limit:
                findings.append(_finding("warn", "hermes", label, f"{used}/{limit} Zeichen ({used * 100 // limit} %) – bald voll, konsolidieren"))
            if raw.strip() and ENTRY_DELIMITER.strip() not in raw and len(raw) > 400:
                findings.append(_finding("warn", "hermes", label, "kein §-Trenner – Freitext statt Einträgen? Hermes behandelt das als Drift"))
            dupes = {e for e in entries if entries.count(e) > 1}
            if dupes:
                findings.append(_finding("warn", "hermes", label, f"{len(dupes)} doppelte Einträge"))
            for entry in entries:
                for p in PATH_RE.findall(entry):
                    resolved = Path(os.path.expanduser(p))
                    if not resolved.exists():
                        findings.append(_finding("warn", "hermes", label, f"Pfad existiert nicht: {p}"))
            if fname == "USER.md" and name != "default" and enabled and entries != default_user_entries:
                findings.append(_finding("info", "hermes", label, "weicht von default/USER.md ab – wird beim nächsten Sync angeglichen"))
    return findings, overview


def lint_sources(repo: Path, today: date) -> list[dict]:
    findings = []
    mem_dir = repo / "memory"
    for path in sorted(mem_dir.glob("*.md")):
        rel = f"memory/{path.name}"
        text = path.read_text(encoding="utf-8")
        stand = parse_stand(text)
        changed = _git_last_change(repo, rel)
        if stand is None:
            findings.append(_finding("info", "quelle", rel, "kein <!-- Stand: … -->-Kopf"))
            continue
        max_days = STAND_MAX_DAYS.get(path.name, STAND_MAX_DAYS_DEFAULT)
        age = (today - stand).days
        if age > max_days:
            findings.append(_finding("warn", "quelle", rel, f"Stand {stand:%m/%Y} ist {age} Tage alt (Grenze {max_days}) – Inhalt prüfen"))
        if changed and _months_between(stand, changed) >= 1:
            findings.append(_finding("warn", "quelle", rel, f"zuletzt geändert {changed:%d.%m.%Y}, Stand-Kopf aber {stand:%m/%Y} – Kopf nachziehen"))
    return findings


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.S)
LINK_RE = re.compile(r"\]\(([^)#\s]+\.md)\)")


def lint_claude() -> list[dict]:
    findings = []
    if not CLAUDE_PROJECTS.is_dir():
        return findings
    for mem_dir in sorted(CLAUDE_PROJECTS.glob("*/memory")):
        project = mem_dir.parent.name
        files = {p.name for p in mem_dir.glob("*.md")} - {"MEMORY.md"}
        index = mem_dir / "MEMORY.md"
        if not files and not index.exists():
            continue
        linked = set(LINK_RE.findall(index.read_text(encoding="utf-8"))) if index.exists() else set()
        linked = {Path(l).name for l in linked}
        for missing in sorted(linked - files):
            findings.append(_finding("warn", "claude", f"{project}/MEMORY.md", f"Index verweist auf fehlende Datei {missing}"))
        for orphan in sorted(files - linked):
            findings.append(_finding("info", "claude", f"{project}/{orphan}", "nicht im MEMORY.md-Index"))
        for fname in sorted(files):
            text = (mem_dir / fname).read_text(encoding="utf-8")
            fm = FRONTMATTER_RE.match(text)
            if not fm:
                findings.append(_finding("warn", "claude", f"{project}/{fname}", "kein Frontmatter"))
            elif not re.search(r"^name:", fm[1], re.M) or not re.search(r"^description:", fm[1], re.M):
                findings.append(_finding("warn", "claude", f"{project}/{fname}", "Frontmatter ohne name/description"))
    return findings


def cmd_lint(repo: Path, out: Path | None) -> dict:
    today = date.today()
    hermes_findings, overview = lint_hermes()
    findings = hermes_findings + lint_sources(repo, today) + lint_claude()
    order = {"error": 0, "warn": 1, "info": 2}
    findings.sort(key=lambda f: (order[f["level"]], f["area"], f["file"]))
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "counts": {lvl: sum(f["level"] == lvl for f in findings) for lvl in order},
        "findings": findings,
        "hermes": overview,
    }
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(out, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    default_repo = Path(os.environ.get("AI_KNOWLEDGE_DATA_DIR", Path.home() / "Projekte" / "ai-knowledge-data"))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, default=default_repo)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mirror")
    pu = sub.add_parser("propagate-user")
    pu.add_argument("--dry-run", action="store_true")
    li = sub.add_parser("lint")
    li.add_argument("--out", type=Path, default=STATE_DIR / "lint.json")
    li.add_argument("--quiet", action="store_true", help="nur Zusammenfassung ausgeben")
    args = ap.parse_args(argv)

    if args.cmd == "mirror":
        for line in cmd_mirror(args.repo):
            print(f"gespiegelt: {line}")
    elif args.cmd == "propagate-user":
        for r in cmd_propagate_user(args.dry_run):
            extra = f", {len(r['extra_entries'])} eigene Einträge" if r["extra_entries"] else ""
            extra += f" gesichert in {r['backup']}" if r["backup"] else ""
            print(f"USER.md -> {r['profile']}: {r['action']}{extra}")
    elif args.cmd == "lint":
        report = cmd_lint(args.repo, args.out)
        c = report["counts"]
        print(f"Lint: {c['error']} Fehler, {c['warn']} Warnungen, {c['info']} Hinweise")
        if not args.quiet:
            for f in report["findings"]:
                print(f"  [{f['level']}] {f['area']}: {f['file']} – {f['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
