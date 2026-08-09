# AI Knowledge Ecosystem

Eine zentrale Wissensdatenbank fuer alle deine KI-Systeme — Claude, ChatGPT, Gemini,
Mistral, Copilot.

## Worum geht es?

Wenn du mit mehreren KIs arbeitest, kennt jede nur das, was du ihr gerade erzaehlt hast.
Dieses Projekt aendert das. Es besteht aus zwei Teilen, die unabhaengig voneinander
funktionieren:

**1. Die Pipeline** — du exportierst deine Chatverlaeufe aus den KIs, ein Python-Skript
liest sie ein, extrahiert das Wissen daraus, entfernt Duplikate, sortiert alles in
Kategorien und erzeugt fertige System-Prompts. Die kopierst du in das Instructions-Feld
der jeweiligen KI.

**2. Die Memory-Module** — handgepflegte Markdown-Dateien in `memory/`, die Claude Code
bei jedem Start mitliest. Ein Symlink (`~/.claude/CLAUDE.md` → `memory/CLAUDE.md`) reicht
dafuer aus.

**Das Ergebnis:** Egal welche KI du oeffnest — sie weiss schon Bescheid.

> **Dieses Repo ist eine Blanko-Vorlage.** Es enthaelt bewusst keine persoenlichen Daten:
> alle Dateien unter `memory/` sind Platzhalter, `knowledge-base/` und `prompts/` sind
> leer. Deine echten Daten gehoeren in eine **private Kopie**.

---

## Schnellstart

### 1. Private Kopie erstellen

Oben rechts auf **"Use this template" → "Create a new repository"**:

- Repository name: z.B. `ai-knowledge-data`
- Visibility: **Private** ← wichtig
- "Create repository"

Danach lokal klonen:

```bash
git clone https://github.com/DEIN_USERNAME/ai-knowledge-data
cd ai-knowledge-data
pip install -r requirements.txt
```

In der privaten Kopie die `.gitignore` anpassen: die Bloecke fuer `knowledge-base/` und
`prompts/` entfernen, damit dein Wissen dort versioniert wird. Die Bloecke fuer
`exports/` und `claude-sync/` bleiben stehen.

### 2. Memory-Module ausfuellen

```bash
# Symlink ~/.claude/CLAUDE.md -> <repo>/memory/CLAUDE.md
bash setup.sh          # Linux/macOS
.\setup.ps1            # Windows (PowerShell als Admin oder Developer Mode)
```

Danach die Platzhalter in `memory/` durch deine Angaben ersetzen:

| Datei | Inhalt | Wird geladen |
|---|---|---|
| `CLAUDE.md` | Einstiegspunkt: Regeln, Modul-Uebersicht | immer (Symlink) |
| `CORE_IDENTITY.md` | Wer du bist — kurz | immer (per `@`-Import) |
| `CURRENT_CONTEXT.md` | Aktueller Stand, laufende Projekte | themenabhaengig |
| `WORK_SKILLS.md` | Tech-Stack, Werdegang, Ziele | themenabhaengig |
| `AI_COLLABORATION.md` | Langfassung der Zusammenarbeitsregeln | themenabhaengig |

Die Trennung ist der eigentliche Trick: Nur `CLAUDE.md` und die per `@` importierten
Module kosten in **jeder** Session Kontext. Alles andere wird erst gelesen, wenn das
Thema passt. Halte die Import-Liste deshalb kurz.

### 3. Exports herunterladen

| KI | Wo exportieren? |
| --- | --- |
| Claude | claude.ai → Einstellungen → Daten exportieren |
| ChatGPT | chatgpt.com → Einstellungen → Daten exportieren |
| Gemini | takeout.google.com → Gemini Apps |
| Mistral | chat.mistral.ai → Einstellungen → Daten exportieren |
| Copilot | account.microsoft.com → Datenschutz → Aktivitaetsverlauf herunterladen |

Dateien nach `exports/` legen (gitignored). Die erwarteten Dateinamen stehen in
`config.json` — fehlende Dateien werden uebersprungen, du brauchst also nicht alle fuenf.

Eigene Notizen als zusaetzliche Quelle: `.md`-Dateien nach `exports/manual/` legen, sie
werden mit eingelesen.

### 4. Pipeline ausfuehren

```bash
python -m scripts.pipeline                 # nutzt config.json
python -m scripts.pipeline config.local.json   # eigene Konfiguration
```

Die Pipeline schreibt `knowledge-base/` **bei jedem Lauf komplett neu** — von Hand dort
eingefuegte Dateien gehen verloren. Eigene Inhalte gehoeren nach `exports/manual/`.

### 5. Prompts in die KIs einspeisen

| Datei | Ziel |
|---|---|
| `prompts/claude_project.md` | claude.ai → Projects → Project Instructions |
| `prompts/chatgpt_custom_gpt.md` | Custom GPT → Instructions |
| `prompts/gemini_gem.md` | Gemini → Gems → Instructions |
| `prompts/mistral_agent.md` | chat.mistral.ai → Agents → Instructions |
| `prompts/copilot_gpt.md` | copilot.microsoft.com → Copilot GPTs → Instructions |

Die Laengenbegrenzung je Plattform steht in `config.json` unter `max_prompt_chars`; wird
sie ueberschritten, kuerzt die Pipeline und weist im Log darauf hin.

---

## Wie die Pipeline arbeitet

```text
exports/  →  extractors.py  →  normalize.py  →  deduplicate.py  →  injectors.py  →  prompts/
                                     ↓
                              knowledge-base/
```

| Schritt | Datei | Was passiert |
|---|---|---|
| Einlesen | `scripts/extractors.py` | Pro Plattform ein Parser. Gemini = HTML (Takeout), der Rest = JSON. Fehlende Dateien werden uebersprungen. |
| Normalisieren | `scripts/normalize.py` | Kategorisiert per Stichwortliste aus `config.json`, vergibt UUIDs, schreibt `.md` mit YAML-Frontmatter nach `knowledge-base/<kategorie>/`. |
| Entdoppeln | `scripts/deduplicate.py` | Entfernt Doppeleintraege. Abschaltbar via `"deduplicate": false`. |
| Prompts bauen | `scripts/injectors.py` | Setzt je Plattform einen passenden Rahmen um die Wissensbasis und kuerzt auf das Limit. |

Kategorien und ihre Stichwoerter aenderst du in `config.json` → `categories`. Die
Zuordnung ist reines Keyword-Matching, kein Modellaufruf — schnell, aber nur so gut wie
deine Stichwortliste.

---

## Struktur

```text
ai-knowledge-ecosystem/
├── memory/                  # Handgepflegte Module (hier: Blanko-Vorlagen)
│   ├── CLAUDE.md            # Einstiegspunkt, Ziel des Symlinks
│   ├── CORE_IDENTITY.md
│   ├── CURRENT_CONTEXT.md
│   ├── WORK_SKILLS.md
│   └── AI_COLLABORATION.md
│
├── knowledge-base/          # Generierte Wissensdatenbank (leer im Template)
│   ├── personal/  projects/  technical/
│   └── business/  creative/  general/
│
├── exports/                 # Rohdaten der KIs — niemals committen
│   └── manual/              # Eigene .md-Notizen als zusaetzliche Quelle
│
├── prompts/                 # Generierte System-Prompts je KI
│
├── scripts/
│   ├── pipeline.py          # Einstiegspunkt: python -m scripts.pipeline
│   ├── extractors.py  normalize.py  deduplicate.py  injectors.py
│   └── install-all-plugins.sh   # optional: Claude-Code-Plugins in einem Rutsch
│
├── claude-sync/             # Settings + Auto-Memory auf weitere Rechner bringen
│   ├── README.md
│   ├── settings.example.json
│   └── apply.ps1
│
├── setup.sh · setup.ps1     # Legt den ~/.claude/CLAUDE.md-Symlink an
├── update_memory.sh         # memory/ mit dem Repo abgleichen (pull/push)
├── config.json · requirements.txt
└── .github/workflows/sync.yml
```

## GitHub Actions

`.github/workflows/sync.yml` fuehrt die Pipeline taeglich um 03:00 UTC aus und ist
manuell ausloesbar. Optionales Secret unter *Settings → Secrets*:

- `ANTHROPIC_API_KEY` — nur noetig, wenn du die Deduplizierung auf Modellbasis erweiterst

Im oeffentlichen Template laeuft der Workflow ins Leere, weil es keine `exports/` gibt.
Sinnvoll wird er erst in der privaten Kopie.

## Mehrere Rechner

`claude-sync/` uebertraegt Claude-Code-Einstellungen und Auto-Memory auf weitere Systeme
(u.a. Windows via `apply.ps1`). Details in `claude-sync/README.md`.

## Voraussetzungen

- Python 3.10 oder neuer
- `pip install -r requirements.txt`
- Optional: [Claude Code](https://claude.com/claude-code) fuer die Memory-Module

## Datenschutz

Dieses Repo ist die **oeffentliche Vorlage** und enthaelt keine persoenlichen Daten.
Beim Nachbauen drei Regeln:

1. **Die Arbeitskopie ist privat.** `memory/`, `knowledge-base/` und `prompts/` enthalten
   nach kurzer Nutzung mehr ueber dich als jedes Social-Media-Profil.
2. **`exports/` bleibt immer lokal** — Rohverlaeufe enthalten alles, auch das, was du
   laengst vergessen hast.
3. **Keys und Passwoerter gehoeren in keine committete Datei.** Git vergisst nichts: ein
   spaeter geloeschter Key steht weiterhin in der History. Deshalb sind
   `claude-sync/settings.json` und `claude-sync/auto-memory/` gitignored und es gibt nur
   eine `settings.example.json` mit Platzhaltern.

Wenn dir doch einmal ein Key durchrutscht: rotieren, nicht nur loeschen.
