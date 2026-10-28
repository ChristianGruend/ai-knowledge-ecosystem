(function () {
  "use strict";
  // Dashboard-Tab „Memory“: Hermes-Memories aller Profile, Prüfbefunde und Sync mit ai-knowledge-data.
  // Kein Build-Schritt – React und UI-Komponenten kommen aus dem Plugin-SDK des Dashboards.
  const SDK = window.__HERMES_PLUGIN_SDK__;
  if (!SDK || !window.__HERMES_PLUGINS__) return;

  const React = SDK.React;
  const h = React.createElement;
  const { useState, useEffect, useCallback, useToast } = SDK.hooks;
  const C = SDK.components;
  const API = "/api/plugins/wissensablage";

  const LEVEL = {
    error: { label: "Fehler", cls: "wa-error" },
    warn: { label: "Warnung", cls: "wa-warn" },
    info: { label: "Hinweis", cls: "wa-info" },
  };
  const AREA = { hermes: "Hermes", quelle: "Quelle", claude: "Claude Code" };

  function fmtTime(iso) {
    if (!iso) return "–";
    const d = new Date(iso);
    return isNaN(d) ? iso : d.toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" });
  }

  function fmtUsec(value) {
    // systemd liefert z. B. "Wed 2026-10-28 21:00:00 CET" oder "n/a"
    return !value || value === "n/a" || value === "0" ? "–" : value.replace(/^\w{2,3} /, "");
  }

  function Usage({ chars, limit }) {
    const pct = Math.min(100, Math.round((chars * 100) / limit));
    const cls = pct > 100 ? "wa-error" : pct > 85 ? "wa-warn" : "wa-ok";
    return h("div", { className: "wa-usage" },
      h("div", { className: "wa-bar" }, h("div", { className: "wa-fill " + cls, style: { width: pct + "%" } })),
      h("span", { className: "wa-muted" }, chars + " / " + limit + " Zeichen (" + pct + " %)"));
  }

  function MemoryFile({ item }) {
    return h("details", { className: "wa-file" },
      h("summary", null,
        h("strong", null, item.file),
        " · " + item.entries.length + " Einträge",
        h(Usage, { chars: item.chars, limit: item.limit })),
      h("ol", { className: "wa-entries" }, item.entries.map((e, i) => h("li", { key: i }, e))));
  }

  function Profiles({ hermes }) {
    const byProfile = {};
    (hermes || []).forEach((item) => { (byProfile[item.profile] = byProfile[item.profile] || []).push(item); });
    const names = Object.keys(byProfile);
    if (!names.length) return h("p", { className: "wa-muted" }, "Noch keine Prüfung gelaufen.");
    return h("div", { className: "wa-grid" }, names.map((name) =>
      h(C.Card, { key: name },
        h(C.CardHeader, null, h(C.CardTitle, null, name,
          byProfile[name][0].enabled ? null : h(C.Badge, { variant: "outline", className: "wa-badge" }, "Memory aus"))),
        h(C.CardContent, null, byProfile[name].map((item) => h(MemoryFile, { key: item.file, item }))))));
  }

  function Findings({ lint }) {
    if (!lint) return h("p", { className: "wa-muted" }, "Noch keine Prüfung gelaufen.");
    if (!lint.findings.length) return h("p", null, "Keine Befunde – alles sauber.");
    return h("ul", { className: "wa-findings" }, lint.findings.map((f, i) =>
      h("li", { key: i },
        h("span", { className: "wa-pill " + LEVEL[f.level].cls }, LEVEL[f.level].label),
        h("span", { className: "wa-area" }, AREA[f.area] || f.area),
        h("code", null, f.file),
        h("span", null, " – " + f.message))));
  }

  function MemoryPage() {
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(null);
    const toast = useToast ? useToast() : null;
    const notify = (msg, kind) => (toast && toast.showToast ? toast.showToast(msg, kind) : console.log(msg));

    const load = useCallback(() =>
      SDK.fetchJSON(API + "/status").then(setData).catch((e) => notify("Status nicht lesbar: " + e.message, "error")), []);

    useEffect(() => { load(); }, [load]);

    const runSync = () => {
      const before = data && data.sync ? data.sync.finished_at : null;
      setBusy("sync");
      SDK.fetchJSON(API + "/sync", { method: "POST" })
        .then(() => {
          let tries = 0;
          const poll = setInterval(() => {
            tries += 1;
            SDK.fetchJSON(API + "/status").then((d) => {
              setData(d);
              const done = d.sync && d.sync.finished_at !== before;
              if (done || tries > 60) {
                clearInterval(poll);
                setBusy(null);
                notify(done ? "Sync: " + d.sync.message : "Sync läuft noch – siehe Log", done && d.sync.result === "ok" ? "success" : "error");
              }
            });
          }, 3000);
        })
        .catch((e) => { setBusy(null); notify("Sync nicht gestartet: " + e.message, "error"); });
    };

    const runLint = () => {
      setBusy("lint");
      SDK.fetchJSON(API + "/lint", { method: "POST" })
        .then(() => load())
        .then(() => notify("Prüfung aktualisiert", "success"))
        .catch((e) => notify("Prüfung fehlgeschlagen: " + e.message, "error"))
        .finally(() => setBusy(null));
    };

    if (!data) return h("div", { className: "wa-page" }, h("p", { className: "wa-muted" }, "Lade …"));

    const sync = data.sync || {};
    const timer = data.units["memory-sync.timer"] || {};
    const path = data.units["memory-sync.path"] || {};
    const counts = data.lint ? data.lint.counts : null;

    return h("div", { className: "wa-page" },
      h("div", { className: "wa-head" },
        h("div", null,
          h("h1", null, "Memory"),
          h("p", { className: "wa-muted" }, "Hermes-Memories, Prüfbefunde und Sync mit ", h("code", null, data.repo))),
        h("div", { className: "wa-actions" },
          h(C.Button, { onClick: runLint, disabled: !!busy, variant: "outline" }, busy === "lint" ? "Prüfe …" : "Neu prüfen"),
          h(C.Button, { onClick: runSync, disabled: !!busy }, busy === "sync" ? "Synchronisiere …" : "Jetzt synchronisieren"))),

      h("div", { className: "wa-grid wa-stats" },
        h(C.Card, null, h(C.CardContent, null,
          h("div", { className: "wa-muted" }, "Letzter Sync"),
          h("div", { className: "wa-big" },
            h("span", { className: "wa-pill " + (sync.result === "ok" ? "wa-ok" : sync.result ? "wa-error" : "wa-info") }, sync.result || "unbekannt"),
            " " + fmtTime(sync.finished_at)),
          h("div", { className: "wa-muted" }, sync.message || ""))),
        h(C.Card, null, h(C.CardContent, null,
          h("div", { className: "wa-muted" }, "Repo"),
          h("div", { className: "wa-big" }, h("code", null, (sync.last_commit || "–").slice(0, 60))),
          h("div", { className: "wa-muted" }, "ungepusht: " + (sync.unpushed_commits ?? "–")))),
        h(C.Card, null, h(C.CardContent, null,
          h("div", { className: "wa-muted" }, "Auslöser"),
          h("div", null, "Timer, nächster Lauf: " + fmtUsec(timer.NextElapseUSecRealtime)),
          h("div", null, "Sofort bei Änderung: " + (path.ActiveState === "active" ? "aktiv" : "aus")))),
        h(C.Card, null, h(C.CardContent, null,
          h("div", { className: "wa-muted" }, "Prüfung " + (data.lint ? fmtTime(data.lint.generated_at) : "")),
          counts ? h("div", { className: "wa-big" },
            h("span", { className: "wa-pill wa-error" }, counts.error), " ",
            h("span", { className: "wa-pill wa-warn" }, counts.warn), " ",
            h("span", { className: "wa-pill wa-info" }, counts.info)) : "–"))),

      h("h2", null, "Befunde"),
      h(Findings, { lint: data.lint }),

      h("h2", null, "Hermes-Profile"),
      h("p", { className: "wa-muted" },
        "default/USER.md ist die Quelle und wird in jedes Profil mit eigenem USER.md verteilt. ",
        "MEMORY.md bleibt pro Profil. Bearbeiten über das Memory-Tool in Hermes, nicht über die Dateien."),
      h(Profiles, { hermes: data.lint ? data.lint.hermes : [] }),

      h("details", { className: "wa-log" },
        h("summary", null, "Sync-Log (letzte 40 Zeilen)"),
        h("pre", null, data.log_tail.join("\n"))));
  }

  window.__HERMES_PLUGINS__.register("wissensablage", MemoryPage);
})();
