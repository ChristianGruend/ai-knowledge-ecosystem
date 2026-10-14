import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from scripts.normalize import normalize_all, save_to_disk, categorize
from scripts.deduplicate import deduplicate
from scripts.injectors import _save_prompt, generate_all_prompts
from scripts.pipeline import run
from scripts.storage import write_if_changed


class RegressionTests(unittest.TestCase):
    def test_ids_and_serialization_are_stable(self):
        raw = [{'source': 'manual', 'content': 'Ein dauerhaft gespeicherter Fakt.'}]
        self.assertEqual(normalize_all(raw, {}), normalize_all(raw, {}))

    def test_existing_notes_survive_rebuild(self):
        with tempfile.TemporaryDirectory() as d:
            note = Path(d) / 'personal' / 'curated.md'
            note.parent.mkdir()
            note.write_text('Manuell gepflegtes Wissen', encoding='utf-8')
            save_to_disk(normalize_all([{'content': 'Ein neuer importierter Fakt.'}], {}), d)
            self.assertTrue(note.exists())
            self.assertEqual(note.read_text(), 'Manuell gepflegtes Wissen')

    def test_shared_prefix_does_not_delete_distinct_facts(self):
        prefix = 'a' * 210
        entries = [{'content': prefix + ' Server A'}, {'content': prefix + ' Server B'}]
        self.assertEqual(len(deduplicate(entries)), 2)

    def test_case_sensitive_facts_are_distinct(self):
        self.assertEqual(len(deduplicate([{'content': 'Pfad /Data'}, {'content': 'Pfad /data'}])), 2)

    def test_word_boundaries(self):
        self.assertEqual(categorize('Speicher server', {'personal': ['ich'], 'technical': ['server']}), 'technical')

    def test_limit_includes_truncation_notice(self):
        with tempfile.TemporaryDirectory() as d:
            _save_prompt(d, 'prompt.md', 'x' * 200, 100)
            self.assertLessEqual(len((Path(d) / 'prompt.md').read_text()), 100)

    def test_memory_only_generation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            memory = root / 'core.md'
            memory.write_text('Mein wichtiger Kernkontext.', encoding='utf-8')
            generate_all_prompts(str(root / 'missing'), str(root / 'prompts'), {'memory_files': [str(memory)]})
            self.assertIn('Mein wichtiger Kernkontext.', (root / 'prompts' / 'chatgpt_custom_gpt.md').read_text())

    def test_repeat_and_partial_import_preserve_history(self):
        with tempfile.TemporaryDirectory() as d:
            entries = normalize_all([{'content': 'Fakt Nummer eins.'}, {'content': 'Fakt Nummer zwei.'}], {})
            save_to_disk(entries, d)
            before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in Path(d).rglob('*.md')}
            save_to_disk(entries[:1], d)
            self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in Path(d).rglob('*.md')})

    def test_exact_duplicates_keep_sources_without_api(self):
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'dummy-not-a-secret'}):
            result = deduplicate([{'source': 'claude', 'content': 'Identischer Fakt'}, {'source': 'manual', 'content': 'Identischer Fakt'}])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['sources'], ['claude', 'manual'])

    def test_failed_atomic_write_preserves_previous_file(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'note.md'
            target.write_text('Original')
            with patch('scripts.storage.os.replace', side_effect=OSError('disk failure')):
                with self.assertRaises(OSError):
                    write_if_changed(target, 'Replacement')
            self.assertEqual(target.read_text(), 'Original')
            self.assertEqual(list(Path(d).iterdir()), [target])

    def test_large_record_is_omitted_whole_and_core_is_first(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            core = root / 'core.md'
            core.write_text('Wichtiger Kernfakt.')
            kb = root / 'kb'; kb.mkdir()
            (kb / 'long.md').write_text('LONG_START' + 'x' * 1000 + 'LONG_END')
            generate_all_prompts(str(kb), str(root / 'prompts'), {'memory_files': [str(core)], 'max_prompt_chars': {'chatgpt': 350}})
            result = (root / 'prompts/chatgpt_custom_gpt.md').read_text()
            self.assertIn('Wichtiger Kernfakt.', result)
            self.assertNotIn('LONG_START', result)
            self.assertLessEqual(len(result), 350)

    def test_missing_explicit_memory_fails_before_output(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                generate_all_prompts(d, d, {'memory_files': [str(Path(d) / 'missing.md')]})
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_frontmatter_does_not_strip_normal_markdown(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); kb = root / 'kb'; kb.mkdir()
            (kb / 'note.md').write_text('Wichtiger Anfang\n\n---\n\nWeiterer Fakt')
            generate_all_prompts(str(kb), str(root / 'prompts'), {})
            self.assertIn('Wichtiger Anfang', (root / 'prompts/chatgpt_custom_gpt.md').read_text())

    def test_empty_sources_preserve_existing_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'chatgpt_custom_gpt.md'; target.write_text('Vorhandenes Wissen')
            generate_all_prompts(str(Path(d) / 'missing'), d, {})
            self.assertEqual(target.read_text(), 'Vorhandenes Wissen')

    def test_pipeline_end_to_end_is_repeatable_from_other_cwd(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'core.md').write_text('Mein stabiler Kernkontext.')
            (root / 'export.json').write_text(json.dumps([{'memory': 'Ein importierter Testfakt.'}]))
            config = root / 'config.json'
            config.write_text(json.dumps({'exports': {'chatgpt': 'export.json'}, 'memory_files': ['core.md'], 'output_dir': 'kb', 'prompts_dir': 'out'}))
            run(str(config))
            def snapshot():
                return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns) for folder in ('kb', 'out') for p in (root / folder).rglob('*.md')}
            before = snapshot()
            run(str(config))
            self.assertEqual(before, snapshot())
            (root / 'export.json').unlink()
            run(str(config))
            self.assertEqual(before, snapshot())
            result = (root / 'out/chatgpt_custom_gpt.md').read_text()
            self.assertIn('Mein stabiler Kernkontext.', result)
            self.assertIn('Ein importierter Testfakt.', result)


if __name__ == '__main__':
    unittest.main()
