# AI Knowledge Ecosystem

My attempt at building a second brain that all my AIs share — Claude, ChatGPT, Gemini,
Mistral, Copilot.

## The problem I had

Every AI starts from zero. New chat, same story: who I am, what I work on, how I want to
be talked to. Type it again. And again. On five different platforms.

So I stopped typing it into chats and started keeping it in one place instead — then
feeding that one place into everything.

Two parts, and they work independently:

**1. The memory modules** — hand-written Markdown in `memory/`, read by Claude Code on
every start. One symlink (`~/.claude/CLAUDE.md` → `memory/CLAUDE.md`) does the whole job.
This is the part I actually use daily.

**2. The pipeline** — I export my chat history from the AIs, a Python script reads it,
pulls the knowledge out, drops duplicates, sorts it into categories, and spits out
ready-made system prompts. Those go into each platform's instructions field.

**When it works:** whichever AI I open already knows the story.

> **This repo is the hollowed-out version.** No personal data in it, on purpose:
> everything under `memory/` is a placeholder, `knowledge-base/` and `prompts/` are
> empty. My real data lives in a separate **private copy** — and yours belongs in one
> of your own.

## Where it actually stands

| Part | State |
|---|---|
| Memory modules + symlink | runs every day, easily the most useful piece |
| Pipeline (exports → prompts) | works, but the categorising is dumb keyword matching |
| Deduplication | roughly fine, no model behind it |
| GitHub Actions workflow | set up, rarely needed in practice |
| `claude-sync/` | grew out of "I need this on the other machine too" |

Still unsolved: the pipeline rewrites `knowledge-base/` from scratch on every run. So
there's no history, and no way to fix a single entry by hand without moving it into
`exports/manual/` first.

> **What this is, and what it isn't.**
> Not a product. Not a framework. Not a finished tool. This is my own setup with the
> personal parts stripped out — a thing I built for myself and put here in case someone
> wants to steal an idea from it. It grows on the side, it changes whenever I find
> something better, and it's exactly as finished as I need it to be.
>
> No support, no guarantees, no roadmap. If you rebuild it: read the code before you run
> it. It's shaped around my day, not yours. Issues are welcome, but I can't promise I'll
> get to them.

---

## Getting started

### 1. Make a private copy

Top right: **"Use this template" → "Create a new repository"**.

- Repository name: something like `ai-knowledge-data`
- Visibility: **Private** ← this one matters
- Create.

Then clone it:

```bash
git clone https://github.com/YOUR_USERNAME/ai-knowledge-data
cd ai-knowledge-data
pip install -r requirements.txt
```

In your private copy, edit `.gitignore`: drop the blocks for `knowledge-base/` and
`prompts/` so your knowledge gets versioned there. Leave the `exports/` and
`claude-sync/` blocks alone.

### 2. Fill in the memory modules

```bash
# symlinks ~/.claude/CLAUDE.md -> <repo>/memory/CLAUDE.md
bash setup.sh          # Linux/macOS
.\setup.ps1            # Windows (PowerShell as admin, or Developer Mode on)
```

Then replace the placeholders in `memory/`:

| File | Holds | Loaded |
|---|---|---|
| `CLAUDE.md` | entry point: rules, module index | always (the symlink) |
| `CORE_IDENTITY.md` | who you are — keep it short | always (via `@` import) |
| `CURRENT_CONTEXT.md` | what's going on right now, running projects | on topic |
| `WORK_SKILLS.md` | stack, background, goals | on topic |
| `AI_COLLABORATION.md` | the long version of how you want to work together | on topic |

The split is the whole trick. Only `CLAUDE.md` and whatever it `@`-imports costs context
in **every** session. Everything else gets read when the topic comes up. So keep that
import list short — I've bloated it twice and regretted it both times.

### 3. Grab your exports

| AI | Where |
| --- | --- |
| Claude | claude.ai → Settings → Export data |
| ChatGPT | chatgpt.com → Settings → Export data |
| Gemini | takeout.google.com → Gemini Apps |
| Mistral | chat.mistral.ai → Settings → Export data |
| Copilot | account.microsoft.com → Privacy → Download activity history |

Drop the files in `exports/` (gitignored). Expected filenames are in `config.json` —
missing ones are skipped, so you don't need all five.

Own notes as an extra source: put `.md` files in `exports/manual/` and they get read in
with the rest.

### 4. Run it

```bash
python -m scripts.pipeline                     # uses config.json
python -m scripts.pipeline config.local.json   # your own config
```

Heads up: `knowledge-base/` is **rewritten from scratch** every run. Anything you paste
in there by hand is gone. Own content goes in `exports/manual/`.

### 5. Feed the prompts back in

| File | Goes to |
|---|---|
| `prompts/claude_project.md` | claude.ai → Projects → Project Instructions |
| `prompts/chatgpt_custom_gpt.md` | Custom GPT → Instructions |
| `prompts/gemini_gem.md` | Gemini → Gems → Instructions |
| `prompts/mistral_agent.md` | chat.mistral.ai → Agents → Instructions |
| `prompts/copilot_gpt.md` | copilot.microsoft.com → Copilot GPTs → Instructions |

Per-platform length limits live in `config.json` under `max_prompt_chars`. Go over, and
the pipeline truncates and says so in the log.

---

## How the pipeline works

```text
exports/  →  extractors.py  →  normalize.py  →  deduplicate.py  →  injectors.py  →  prompts/
                                     ↓
                              knowledge-base/
```

| Step | File | What happens |
|---|---|---|
| Read | `scripts/extractors.py` | One parser per platform. Gemini is HTML (Takeout), the rest is JSON. Missing files get skipped. |
| Normalise | `scripts/normalize.py` | Categorises by keyword list from `config.json`, assigns UUIDs, writes `.md` with YAML frontmatter into `knowledge-base/<category>/`. |
| Dedupe | `scripts/deduplicate.py` | Drops duplicates. Turn off with `"deduplicate": false`. |
| Build prompts | `scripts/injectors.py` | Wraps the knowledge base in a per-platform framing and trims to the limit. |

Categories and their keywords live in `config.json` → `categories`. It's plain keyword
matching, no model call — fast, and only ever as good as your keyword list. Mine is
mediocre and I keep meaning to fix it.

---

## Layout

```text
ai-knowledge-ecosystem/
├── memory/                  # hand-written modules (placeholders in here)
│   ├── CLAUDE.md            # entry point, target of the symlink
│   ├── CORE_IDENTITY.md
│   ├── CURRENT_CONTEXT.md
│   ├── WORK_SKILLS.md
│   └── AI_COLLABORATION.md
│
├── knowledge-base/          # generated knowledge base (empty here)
│   ├── personal/  projects/  technical/
│   └── business/  creative/  general/
│
├── exports/                 # raw AI exports — never commit these
│   └── manual/              # own .md notes as an extra source
│
├── prompts/                 # generated system prompts, one per AI
│
├── scripts/
│   ├── pipeline.py          # entry point: python -m scripts.pipeline
│   ├── extractors.py  normalize.py  deduplicate.py  injectors.py
│   └── install-all-plugins.sh   # optional: install Claude Code plugins in one go
│
├── claude-sync/             # carry settings + auto-memory to another machine
│   ├── README.md
│   ├── settings.example.json
│   └── apply.ps1
│
├── setup.sh · setup.ps1     # creates the ~/.claude/CLAUDE.md symlink
├── update_memory.sh         # sync memory/ with the repo (pull/push)
├── config.json · requirements.txt
└── .github/workflows/sync.yml
```

## GitHub Actions

`.github/workflows/sync.yml` runs the pipeline daily at 03:00 UTC and can be triggered by
hand. Optional secret under *Settings → Secrets*:

- `ANTHROPIC_API_KEY` — only if you extend deduplication to use a model

In this public copy the workflow runs into nothing, because there's no `exports/`. It
only makes sense in the private copy.

## More than one machine

`claude-sync/` carries Claude Code settings and auto-memory over to other systems
(including Windows, via `apply.ps1`). Details in `claude-sync/README.md`.

## Requirements

- Python 3.10+
- `pip install -r requirements.txt`
- Optional: [Claude Code](https://claude.com/claude-code) for the memory modules

## About the data

This repo is the hollowed-out version and holds nothing personal — that's the entire
reason there are two repos. Three rules I set for myself, and they apply just as much if
you rebuild this:

1. **The working copy stays private.** After a few weeks, `memory/`, `knowledge-base/`
   and `prompts/` say more about you than any social profile does.
2. **`exports/` never leaves the machine.** Raw chat history contains everything —
   including the parts you'd forgotten you said.
3. **Keys and passwords go in no committed file, ever.** Git doesn't forget: a key you
   delete later is still sitting in the history. That's why `claude-sync/settings.json`
   and `claude-sync/auto-memory/` are gitignored and all you get is a
   `settings.example.json` full of placeholders.

And if one slips through anyway: rotate it. Deleting it isn't enough.
