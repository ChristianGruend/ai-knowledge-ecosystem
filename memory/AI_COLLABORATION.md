# AI_COLLABORATION.md — Vorlage

> Blanko-Modul aus dem oeffentlichen Template. Themenabhaengig nachladen (Meta-Fragen zur
> Zusammenarbeit, Prompt- und Memory-Setup). Hier steht die **Langfassung** dessen, was in
> `CLAUDE.md` nur als Kurzregel auftaucht — nicht doppeln, sondern vertiefen.

## Warum dieses Memory-System

Jede KI startet bei null. Dieses System haelt die Antworten auf immer wiederkehrende
Fragen ("wer bist du", "womit arbeitest du", "wie willst du angesprochen werden") an
einem Ort und speist sie automatisch ein.

Zwei Wege, dasselbe Ziel:

1. **Claude Code** liest `~/.claude/CLAUDE.md` (Symlink auf `memory/CLAUDE.md`) bei jedem
   Start — plus alles, was dort per `@` importiert wird.
2. **Andere KIs** bekommen den generierten System-Prompt aus `prompts/` in ihr jeweiliges
   Instructions-Feld (Projects, Custom GPT, Gem, Agent).

## Regeln fuer die Zusammenarbeit (Langfassung)

- Anrede und Tonfall …
- Umgang mit Unsicherheit: lieber "weiss ich nicht" als geraten
- Umgang mit Fehlern: kurz korrigieren, nicht ausufernd entschuldigen
- Wann nachfragen, wann einfach machen …

## Memory-Pflege

- Eine Information steht an **genau einer** Stelle. Taucht sie zweimal auf, widerspricht
  sie sich frueher oder spaeter.
- `CURRENT_CONTEXT.md` regelmaessig durchgehen — es veraltet am schnellsten.
- Neue Erkenntnis aus einem Chat? Ins passende Modul schreiben, nicht in den Chat-Verlauf
  verlassen.
- Nach jeder Aenderung: `bash update_memory.sh --push` (siehe README).

## Standby-Workflow

Wie soll die KI reagieren, wenn du laenger nichts sagst oder eine Aufgabe im Hintergrund
laeuft? Hier festhalten, damit es nicht jedes Mal neu ausgehandelt wird.
