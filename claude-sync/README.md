# claude-sync

Traegt Claude-Code-Einstellungen und Auto-Memory von einem System auf ein anderes
(z.B. Linux → Windows 11), damit alle Rechner denselben Stand haben.

## Inhalt

| Datei | Entspricht |
|---|---|
| `settings.example.json` | Vorlage fuer `~/.claude/settings.json` |
| `settings.json` | deine echte Kopie — **gitignored**, siehe Warnung unten |
| `auto-memory/` | `~/.claude/projects/<projekt-key>/memory/` — **gitignored** |
| `apply.ps1` | spielt beides auf Windows ein |

> ⚠️ **`settings.json` und `auto-memory/` stehen bewusst in der `.gitignore`.**
> `settings.json` enthaelt in der Praxis API-Keys und teils Passwoerter im Klartext,
> `auto-memory/` enthaelt persoenliche Notizen. Beides gehoert selbst in ein privates
> Repo nur, wenn dir klar ist, dass Git jede Version dauerhaft aufbewahrt — ein
> spaeter geloeschter Key bleibt in der History lesbar.
> Zum Start: `cp settings.example.json settings.json` und die Platzhalter fuellen.

## Einrichtung auf Windows 11

### 1. Voraussetzungen
```powershell
# Node.js + Claude Code CLI
winget install OpenJS.NodeJS.LTS
npm install -g @anthropic-ai/claude-code

# GitHub CLI + Login (fuer die private Kopie)
winget install GitHub.cli
gh auth login
```

### 2. Private Kopie klonen
```powershell
gh repo clone DEIN_USERNAME/ai-knowledge-data
cd ai-knowledge-data
```

### 3. CLAUDE.md-Symlink (Memory-Module)
```powershell
# als Admin oder mit aktiviertem Developer Mode
.\setup.ps1
```

### 4. Claude einmal starten (legt `~/.claude/projects/<key>/` an)
```powershell
cd $HOME
claude
# danach mit /exit beenden
```

### 5. Settings + Auto-Memory einspielen
```powershell
cd <pfad-zum-repo>\claude-sync
.\apply.ps1
```

`apply.ps1` legt vorher ein Backup der bestehenden `settings.json` an
(`settings.json.bak`) und bricht ab, wenn mehrere Projekt-Verzeichnisse existieren —
dann waehlst du das richtige selbst aus.

## Sync aktuell halten

Nach Aenderungen an `~/.claude/settings.json` oder am Auto-Memory eines Systems:

```bash
cp ~/.claude/settings.json claude-sync/settings.json
cp -r ~/.claude/projects/<projekt-key>/memory/* claude-sync/auto-memory/
```

Beides ist gitignored — fuer den Transport auf andere Rechner entweder die
`.gitignore` in **deiner privaten Kopie** bewusst anpassen oder die Dateien ausserhalb
von Git uebertragen (USB, Syncthing, verschluesselter Speicher).
