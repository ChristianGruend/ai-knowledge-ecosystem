# AI Knowledge Ecosystem

Zentrale Wissensdatenbank fuer alle KI-Systeme (Claude, ChatGPT, Gemini, Mistral, Copilot u.a.)

## Worum geht es?

Wenn du mit mehreren KIs arbeitest, kennt jede nur das, was du ihr erzaehlt hast. Dieses Projekt aendert das:

Du exportierst deine Chatverlaeufe aus Claude, ChatGPT, Gemini, Mistral und Copilot. Eine automatische Pipeline liest diese Daten, extrahiert dein Wissen daraus, entfernt Duplikate und sortiert alles in Kategorien. Daraus entstehen fertige System-Prompts, die du in jede KI einfuegen kannst.

**Das Ergebnis:** Alle deine KIs kennen dich – deine Projekte, Vorlieben, dein technisches Wissen. Egal welche KI du oeffnest, sie weiss schon Bescheid.

## Schnellstart

Dieses Repo ist ein **Template**. Klicke oben auf **"Use this template"** und erstelle dir eine **private Kopie**. In deiner privaten Kopie kannst du dann deine Daten sicher speichern.

### 1. Private Kopie erstellen

Oben rechts auf **"Use this template" > "Create a new repository"** klicken. Dann:
- Repository name: z.B. `ai-knowledge-data`
- Visibility: **Private**
- "Create repository" klicken

Danach lokal klonen:

```bash
git clone https://github.com/DEIN_USERNAME/ai-knowledge-data
cd ai-knowledge-data
pip install -r requirements.txt
```

In deiner privaten Kopie die `.gitignore` anpassen: Die Zeilen fuer `knowledge-base/` und `prompts/` entfernen, damit dein Wissen im privaten Repo gespeichert wird.

### 2. Exports herunterladen

| KI | Wo exportieren? |
| --- | --- |
| Claude | claude.ai > Einstellungen > Daten exportieren |
| ChatGPT | chatgpt.com > Einstellungen > Daten exportieren |
| Gemini | takeout.google.com > Gemini Apps |
| Mistral | chat.mistral.ai > Einstellungen > Daten exportieren |
| Copilot | account.microsoft.com > Datenschutz > Aktivitaetsverlauf herunterladen |

Dateien ablegen in `exports/` (wird nicht gepusht – steht in `.gitignore`)

### 3. Pipeline ausfuehren

```bash
python scripts/pipeline.py
```

### 4. Prompts in KIs einspeisen

- **Claude:** `prompts/claude_project.md` > claude.ai > Projects > Project Instructions
- **ChatGPT:** `prompts/chatgpt_custom_gpt.md` > Custom GPT > Instructions
- **Gemini:** `prompts/gemini_gem.md` > Gems > Instructions
- **Mistral:** `prompts/mistral_agent.md` > chat.mistral.ai > Agents > Instructions
- **Copilot:** `prompts/copilot_gpt.md` > copilot.microsoft.com > Copilot GPTs > Instructions

## Struktur

```text
ai-knowledge-ecosystem/
├── knowledge-base/          # Deine Wissensdatenbank
│   ├── personal/            # Persoenliches Profil
│   ├── projects/            # Projekte & Aufgaben
│   ├── technical/           # Technisches Wissen
│   ├── business/            # Business-Kontext
│   ├── creative/            # Kreatives
│   └── general/             # Allgemeines
│
├── exports/                 # Rohdaten von den KIs (nicht committen!)
│
├── prompts/                 # Generierte System-Prompts je KI
│   ├── claude_project.md
│   ├── chatgpt_custom_gpt.md
│   ├── gemini_gem.md
│   ├── mistral_agent.md
│   └── copilot_gpt.md
│
├── scripts/                 # Python-Pipeline
│   ├── extractors.py
│   ├── normalize.py
│   ├── deduplicate.py
│   ├── injectors.py
│   └── pipeline.py
│
└── .github/workflows/
    └── sync.yml             # Automatischer Sync via GitHub Actions
```

## GitHub Actions

Der Workflow `.github/workflows/sync.yml` fuehrt die Pipeline automatisch aus.

Benoetigte Secrets (in Repo-Einstellungen unter *Settings > Secrets*):

- `ANTHROPIC_API_KEY` – fuer KI-Deduplizierung (optional)

## Datenschutz

Dieses Template-Repo enthaelt **keine persoenlichen Daten**.

Fuer die Nutzung empfehlen wir eine **private Kopie** (siehe Schnellstart). In der privaten Kopie werden `knowledge-base/` und `prompts/` im Git gespeichert – sicher, weil nur du Zugriff hast. Die `exports/` (Rohdaten) bleiben immer lokal.
