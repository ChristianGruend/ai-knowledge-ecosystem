# CLAUDE.md — Vorlage

> **Das hier ist die Blanko-Vorlage aus dem oeffentlichen Template.**
> `setup.sh` / `setup.ps1` verlinken `~/.claude/CLAUDE.md` auf genau diese Datei.
> In deiner privaten Kopie ersetzt du die Platzhalter durch deine echten Angaben.
> Alles, was hier steht, liest jede Claude-Code-Session bei jedem Start mit —
> halte es deshalb kurz und stelle jede Information genau an einer Stelle ab.

## Memory-Module

**Immer geladen** (echte Imports, werden beim Start eingelesen):

@~/Projekte/ai-knowledge-data/memory/CORE_IDENTITY.md

> Pfad anpassen: er muss auf den Klon **deiner privaten Kopie** zeigen.
> Nimm nur hier auf, was wirklich immer gebraucht wird — jeder Import kostet Kontext
> in jeder Session.

**Themenabhaengig laden** — nicht automatisch im Kontext. Bei passendem Thema per
Read-Tool aus `~/Projekte/ai-knowledge-data/memory/` nachladen:

| Datei | Inhalt | Laden wenn Thema |
|---|---|---|
| `CURRENT_CONTEXT.md` | Aktueller Stand: laufende Projekte, naechste Schritte | Status, To-dos, Planung |
| `WORK_SKILLS.md` | Ausbildung, Tech-Stack, Projektuebersicht, Ziele | Skills, Tools, Karriere, Bewerbung |
| `AI_COLLABORATION.md` | Langfassung der KI-Regeln, Memory-System, Workflows | Meta-Fragen zur Zusammenarbeit |

> Weitere Module frei ergaenzen. Sensible Dateien (z.B. gesundheitliche oder
> psychologische Notizen) gehoeren **nur** in diese Tabelle, nie in die Import-Liste
> oben — sonst landen sie in jedem Chat, auch im voellig unpassenden.

Regel: eine Information steht an genau einer Stelle. Was in einem Memory-Modul steht,
wird hier nicht wiederholt.

---

## Zusammenarbeitsregeln

Beispielhafte Regeln — ersetze sie durch deine eigenen:

- Anrede und Sprache festlegen (z.B. immer duzen, Sprache = Eingabesprache)
- Kein Moralisieren, kein Lob ohne Grund, keine langen Einleitungen
- Direkt zum Punkt, maximal 1–2 Rueckfragen
- Themenwechsel einfach mitgehen, nicht kommentieren

**Antwortformat:**
```
1. Kurze Erklaerung (1–3 Saetze)
2. Praktische Schritte
3. [Optional] Tiefe — nur wenn explizit gefragt
```

**Modi** (optional, hilft dem Modell beim Kalibrieren):

| Modus | Trigger | Verhalten |
|---|---|---|
| Exploration | Viele kurze Fragen | Kurz, Optionen |
| Deep Focus | Lange Frage | Strukturierte Tiefe |
| Debugging | Fehler/Code | Hypothesen, Test-Befehle |
| Brainstorming | "Ideen fuer..." | Viel, nicht filtern |
| Planung | "Wie vorgehen?" | Priorisierte Schritte |

## Agenten & Modellwahl

- Subagenten standardmaessig nutzen — sie halten Suchergebnisse, Logs und Dateidumps
  aus dem Hauptkontext heraus.
- **Plan oben, Ausfuehrung unten:** Der Plan entsteht im staerksten Modell, die
  Ausfuehrung geht an das kleinstmoegliche Modell, das die Teilaufgabe sicher schafft.
- Modell explizit setzen, sonst erbt der Subagent das teure Session-Modell.

---

## Repo-Aufteilung — zwei getrennte Repos

| Repo | Sichtbarkeit | Zweck |
|---|---|---|
| `DEIN_USERNAME/ai-knowledge-data` | **privat** | Live-Umgebung mit allen persoenlichen Daten |
| `ChristianGruend/ai-knowledge-ecosystem` | **oeffentlich** | Blanko-Vorlage zum Nachbauen, ohne private Daten |

`~/.claude/CLAUDE.md` ist ein Symlink auf `memory/CLAUDE.md` in der privaten Kopie.
Nichts aus `memory/` oder `knowledge-base/` darf ins oeffentliche Repo.

*⚠️ Private Kopie privat halten — die Memory-Module enthalten persoenliche Daten.*
