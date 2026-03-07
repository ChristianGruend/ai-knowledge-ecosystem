# AI Knowledge Ecosystem

Zentrale Wissensdatenbank fuer alle KI-Systeme (Claude, ChatGPT, Gemini, u.a.)

## Worum geht es?

Wenn du mit mehreren KIs arbeitest, kennt jede nur das, was du ihr erzaehlt hast. Dieses Projekt aendert das:

Du exportierst deine Chatverlaeufe aus Claude, ChatGPT und Gemini. Eine automatische Pipeline liest diese Daten, extrahiert dein Wissen daraus, entfernt Duplikate und sortiert alles in Kategorien. Daraus entstehen fertige System-Prompts, die du in jede KI einfuegen kannst.

**Das Ergebnis:** Alle deine KIs kennen dich – deine Projekte, Vorlieben, dein technisches Wissen. Egal welche KI du oeffnest, sie weiss schon Bescheid.

## Struktur

```
ai-knowledge-ecosystem/
├── 📁 knowledge-base/        # Deine .md-Wissensdatenbank
│   ├── personal/             # Persönliches Profil, Präferenzen
│   ├── projects/             # Projekte & Aufgaben
│   ├── technical/            # Technisches Wissen
│   ├── business/             # Business-Kontext
│   └── general/              # Allgemeines
│
├── 📁 exports/               # Rohdaten von den AIs (nicht committen!)
│   └── .gitkeep
│
├── 📁 prompts/               # Generierte System-Prompts je AI
│   ├── claude_project.md
│   ├── chatgpt_custom_gpt.md
│   └── gemini_gem.md
│
├── 📁 scripts/               # Python-Pipeline
│   ├── extractors.py
│   ├── normalize.py
│   ├── deduplicate.py
│   ├── injectors.py
│   └── pipeline.py
│
└── .github/workflows/
    └── sync.yml              # Täglicher Auto-Sync via GitHub Actions
```

## Schnellstart

### 1. Setup
```bash
git clone https://github.com/DEIN_USERNAME/ai-knowledge-ecosystem
cd ai-knowledge-ecosystem
pip install -r requirements.txt
```

### 2. Exports herunterladen
| AI | Export-Pfad |
|----|------------|
| Claude | claude.ai → Einstellungen → Daten exportieren |
| ChatGPT | chatgpt.com → Einstellungen → Daten exportieren |
| Gemini | takeout.google.com → Gemini Apps |

Dateien ablegen in `exports/` (wird nicht zu GitHub gepusht – steht in `.gitignore`)

### 3. Pipeline ausführen
```bash
python scripts/pipeline.py
```

### 4. Prompts in AIs einspeisen
- **Claude:** `prompts/claude_project.md` → claude.ai → Projects → Project Instructions
- **ChatGPT:** `prompts/chatgpt_custom_gpt.md` → Custom GPT → Instructions
- **Gemini:** `prompts/gemini_gem.md` → Gems → Instructions

## GitHub Actions

Der Workflow `.github/workflows/sync.yml` führt die Pipeline täglich automatisch aus.

Benötigte Secrets (in Repo-Einstellungen unter *Settings → Secrets*):
- `ANTHROPIC_API_KEY` – für KI-Deduplizierung (optional)

## Datenschutz

Dieses Repo enthaelt **keine persoenlichen Daten**. Alle privaten Inhalte bleiben lokal auf deinem Rechner:

- `exports/` – deine exportierten Chatverlaeufe (lokal, in `.gitignore`)
- `knowledge-base/` – dein aufbereitetes Wissen (lokal, in `.gitignore`)
- `prompts/` – die generierten System-Prompts (lokal, in `.gitignore`)

Auf GitHub landen nur die Scripts, die Config und diese README.
