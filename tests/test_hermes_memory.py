import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from scripts import hermes_memory as hm


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class HermesMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.home = root / "hermes"
        self.state = root / "state"
        self.repo = root / "repo"
        _write(self.home / "config.yaml", "model: {}\n")
        self.patches = [patch.object(hm, "HERMES_HOME", self.home), patch.object(hm, "STATE_DIR", self.state),
                        patch.object(hm, "CLAUDE_PROJECTS", root / "claude")]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def _profile(self, name: str, user: str | None = None, config: str = "model: {}\n") -> Path:
        home = self.home / "profiles" / name
        _write(home / "config.yaml", config)
        if user is not None:
            _write(home / "memories" / "USER.md", user)
        return home

    def test_parse_stand_formats(self):
        self.assertEqual(hm.parse_stand("# X\n<!-- Stand: Juli 2026 -->\n"), date(2026, 7, 1))
        self.assertEqual(hm.parse_stand("<!-- Stand: 2026-10-12 -->"), date(2026, 10, 12))
        self.assertEqual(hm.parse_stand("Stand: 3.9.2026"), date(2026, 9, 3))
        self.assertEqual(hm.parse_stand("<!-- Stand: März 2026 -->"), date(2026, 3, 1))
        self.assertIsNone(hm.parse_stand("# ohne Kopf\n"))

    def test_propagate_backs_up_local_profile_edits_and_skips_profiles_without_user_md(self):
        _write(self.home / "memories" / "USER.md", "A\n§\nB")
        coder = self._profile("team-coder", user="A\n§\nalt und eigen")
        self._profile("testlab")  # ohne USER.md: bekommt keins
        self._profile("lokal", user="X", config="memory:\n  memory_enabled: false\n  user_profile_enabled: false\n")

        results = hm.cmd_propagate_user()

        self.assertEqual([r["profile"] for r in results], ["team-coder"])
        self.assertEqual(results[0]["extra_entries"], ["alt und eigen"])
        self.assertEqual(Path(results[0]["backup"]).read_text(encoding="utf-8"), "A\n§\nalt und eigen")
        self.assertEqual((coder / "memories" / "USER.md").read_text(encoding="utf-8"), "A\n§\nB")
        self.assertFalse((self.home / "profiles" / "testlab" / "memories" / "USER.md").exists())
        self.assertEqual((self.home / "profiles" / "lokal" / "memories" / "USER.md").read_text(encoding="utf-8"), "X")
        # zweiter Lauf: nichts mehr zu tun
        self.assertEqual(hm.cmd_propagate_user(), [])

    def test_propagate_dry_run_changes_nothing(self):
        _write(self.home / "memories" / "USER.md", "neu")
        coder = self._profile("team-coder", user="alt")
        results = hm.cmd_propagate_user(dry_run=True)
        self.assertEqual(results[0]["action"], "would-update")
        self.assertEqual((coder / "memories" / "USER.md").read_text(encoding="utf-8"), "alt")
        self.assertFalse((self.state / "propagation.json").exists())

    def test_mirror_uses_profile_layout_and_removes_legacy_flat_files(self):
        _write(self.home / "memories" / "MEMORY.md", "m")
        self._profile("team-coder", user="u")
        _write(self.repo / "hermes-memories" / "MEMORY.md", "alt")  # altes flaches Layout

        hm.cmd_mirror(self.repo)

        files = sorted(str(p.relative_to(self.repo)) for p in (self.repo / "hermes-memories").rglob("*.md"))
        self.assertEqual(files, ["hermes-memories/default/MEMORY.md", "hermes-memories/profiles/team-coder/USER.md"])

    def test_lint_flags_limit_and_missing_paths(self):
        _write(self.home / "memories" / "USER.md", "x" * 1300)
        _write(self.home / "memories" / "MEMORY.md", "Skript liegt in ~/gibt-es-nicht/tool.py")
        report = hm.cmd_lint(self.repo, self.state / "lint.json")
        messages = [f["message"] for f in report["findings"]]
        self.assertTrue(any("bald voll" in m for m in messages))
        self.assertTrue(any("~/gibt-es-nicht/tool.py" in m for m in messages))
        self.assertEqual(json.loads((self.state / "lint.json").read_text())["counts"], report["counts"])


if __name__ == "__main__":
    unittest.main()
