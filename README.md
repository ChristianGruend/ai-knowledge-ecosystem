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
| Deduplication | exact matches only, no model behind it |
| Import history | append-only — nothing gets deleted or overwritten anymore |
| Tests | 15 unit tests, `python -m unittest discover -s tests` |
| GitHub Actions workflow | set up, rarely needed in practice |
| `claude-sync/` | grew out of "I need this on the other machine too" |

Fixed since the first version: the pipeline used to rewrite `knowledge-base/` from
scratch on every run. Now imports only ever get added, and hand edits survive.

Still unsolved: contradictions. If an old chat says one thing and a newer one says the
opposite, both land in the knowledge base. Nothing resolves that automatically — I
clean those up by hand.

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

Run it as often as you like. Imports land in `knowledge-base/_imports/`, one file per
fact, named after the SHA-256 of its text — so the same fact never lands twice, and a
partial export can't wipe anything you imported before. Files that didn't change
don't get touched, so a re-run with nothing new produces an empty `git diff`.

Your own notes can go straight into `knowledge-base/` (any subfolder) — they're kept
and end up in the prompts. Don't edit files in `_imports/`, though: that folder is an
archive. To correct a fact, delete the wrong file and add the right one.

### 5. Feed the prompts back in

| File | Goes to |
|---|---|
| `prompts/claude_project.md` | claude.ai → Projects → Project Instructions |
| `prompts/chatgpt_custom_gpt.md` | Custom GPT → Instructions |
| `prompts/gemini_gem.md` | Gemini → Gems → Instructions |
| `prompts/mistral_agent.md` | chat.mistral.ai → Agents → Instructions |
| `prompts/copilot_gpt.md` | copilot.microsoft.com → Copilot GPTs → Instructions |

Per-platform length limits live in `config.json` under `max_prompt_chars`. Go over, and
the pipeline drops whole entries (never cuts one in half) and leaves a note at the end
of the prompt that something was left out.

What goes in first is set by `memory_files` in `config.json` — an explicit, ordered
list. By default that's `CORE_IDENTITY`, `WORK_SKILLS`, `CURRENT_CONTEXT`, then the
knowledge base. Anything else from `memory/` only gets in if you add it to that list
yourself. That's on purpose: I don't want a deep personal profile to slip into a
ChatGPT prompt just because it sits in the same folder. If a file on the list is
missing, the run stops instead of quietly building a thinner prompt.

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
| Normalise | `scripts/normalize.py` | Categorises by keyword list from `config.json`, drops entries matching `exclude_keywords`, gives each one a SHA-256 ID and writes it as `.md` with YAML frontmatter into `knowledge-base/_imports/`. Existing files are skipped. |
| Dedupe | `scripts/deduplicate.py` | Drops exact duplicates only — case and inner whitespace count, so code and paths stay intact. Sources of identical entries get merged. No data goes to any model API. Turn off with `"deduplicate": false`. |
| Build prompts | `scripts/injectors.py` | Puts `memory_files` first, then everything under `knowledge-base/`, and fits whole entries into each platform's limit. No sources at all → existing prompts stay untouched. |
| Write | `scripts/storage.py` | Atomic writes, and only when the content actually changed. |

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
├── knowledge-base/          # knowledge base (empty here)
│   ├── _imports/            # append-only import archive, one file per fact
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
│   ├── storage.py           # atomic write-if-changed
│   ├── ai-knowledge-sync.sh # pull, mirror auto-memories, commit + push (see below)
│   └── install-all-plugins.sh   # optional: install Claude Code plugins in one go
│
├── tests/                   # python -m unittest discover -s tests
│
├── systemd/                 # memory-sync.service + .timer for ai-knowledge-sync.sh
│
├── claude-sync/             # carry settings + auto-memory to another machine
│   ├── README.md
│   ├── settings.example.json
│   └── apply.ps1
│
├── setup.sh · setup.ps1     # creates the ~/.claude/CLAUDE.md symlink
├── update_memory.sh         # sync memory/ with the repo (pull, or --push [dir])
├── config.json · requirements.txt
└── .github/workflows/       # sync.yml (daily pipeline) · tests.yml (every push/PR)
```

## GitHub Actions

`.github/workflows/sync.yml` runs the pipeline daily at 03:00 UTC and can be triggered by
hand. It needs no secrets — deduplication doesn't call a model anymore. If you set an
`ANTHROPIC_API_KEY` secret back when it did, you can delete it.

In this public copy the workflow runs into nothing, because there's no `exports/`. It
only makes sense in the private copy.

## More than one machine

`claude-sync/` carries Claude Code settings and auto-memory over to other systems
(including Windows, via `apply.ps1`). Details in `claude-sync/README.md`.

To keep the private copy current without thinking about it, `scripts/ai-knowledge-sync.sh`
pulls, mirrors every `~/.claude/projects/*/memory/` into `claude-memories/` (and Hermes
memories into `hermes-memories/`, if present), then commits and pushes. Run it three times
a day with the user units in `systemd/`:

```bash
ln -s "$PWD/scripts/ai-knowledge-sync.sh" ~/.local/bin/ai-knowledge-sync.sh
cp systemd/memory-sync.* ~/.config/systemd/user/
systemctl --user enable --now memory-sync.timer
```

The mirrors hold personal data — only ever let the script run in the private copy.
`No local changes to push.` in `~/.local/share/ai-knowledge-sync.log` means healthy.

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
