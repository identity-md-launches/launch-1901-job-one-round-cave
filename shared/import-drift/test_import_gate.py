"""Line 3 snapshots -> Line 2 policy and HTML; all fixtures stay in scratch."""
import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

import bounded_snapshot
import import_gate as tool


class ImportGateTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'worker.py').write_text('import json\nraise RuntimeError("never run")\n')

    def snapshot(self, name):
        text, evidence = bounded_snapshot.snapshot(self.source)
        path = self.root / name
        path.write_text(text)
        return path, evidence

    def cli(self, *args):
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = tool.main([str(a) for a in args])
        return status, output.getvalue(), error.getvalue()

    def test_real_source_exports_default_refusal_and_explicit_acceptance(self):
        before, _ = self.snapshot('before.csv')
        (self.source / 'worker.py').write_text('import json\nimport csv\n')
        after, _ = self.snapshot('after.csv')
        result = tool.compare(before, after)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['comparison']['summary']['changed'], 1)
        accepted = tool.compare(before, after, max_changed=1, allow_change=['external_imports'])
        self.assertTrue(accepted['accepted'])
        self.assertFalse(accepted['comparison']['equal'])
        self.assertEqual(accepted['comparison']['changed'][0]['fields']['external_imports'],
                         {'before': '["json"]', 'after': '["csv","json"]'})
        self.assertEqual(self.cli(before, after)[0], 1)
        self.assertEqual(self.cli(before, after, '--max-changed', 1,
                                  '--allow-change', 'external_imports')[0], 0)

    def test_added_and_removed_modules_keep_full_rows(self):
        before, _ = self.snapshot('before.csv')
        (self.source / 'worker.py').unlink()
        (self.source / 'replacement.py').write_text('import csv\n')
        after, _ = self.snapshot('after.csv')
        result = tool.compare(before, after, max_added=1, max_removed=1)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['comparison']['added'][0]['values']['module'], 'replacement')
        self.assertEqual(result['comparison']['removed'][0]['values']['module'], 'worker')

    def test_wrong_allowed_column_cannot_hide_dependency_change(self):
        before, _ = self.snapshot('before.csv')
        (self.source / 'worker.py').write_text('import csv\n')
        after, _ = self.snapshot('after.csv')
        result = tool.compare(before, after, max_changed=1, allow_change=['path'])
        self.assertFalse(result['accepted'])
        self.assertEqual(result['violations'][0]['columns'], ['external_imports'])
        for name in ('typo', 'module'):
            with self.assertRaises(ValueError):
                tool.compare(before, after, allow_change=[name])

    def test_warning_equality_is_not_clean_source_claim(self):
        (self.source / 'broken.py').write_text('def broken(\n')
        before, evidence = self.snapshot('before.csv')
        self.assertTrue(evidence['issues'])
        result = tool.compare(before, before)
        self.assertTrue(result['accepted'])
        self.assertIn('absence of scan warnings', result['scope'])

    def test_empty_exports_can_compare(self):
        (self.source / 'worker.py').unlink()
        before, _ = self.snapshot('empty.csv')
        self.assertTrue(tool.compare(before, before)['accepted'])

    def test_schema_refusal_has_no_partial_report(self):
        before, _ = self.snapshot('before.csv')
        after = self.root / 'bad.csv'
        after.write_text('module,value\nworker,x\n')
        status, output, error = self.cli(before, after)
        self.assertEqual((status, output), (2, ''))
        self.assertIn('snapshot columns', json.loads(error)['error'])

    def test_duplicate_and_empty_module_keys_reject(self):
        before, _ = self.snapshot('before.csv')
        rows = list(csv.DictReader(io.StringIO(before.read_text())))
        after = self.root / 'bad.csv'
        for key in ('worker', ''):
            stream = io.StringIO(newline='')
            writer = csv.DictWriter(stream, fieldnames=tool.drift.FIELDS)
            writer.writeheader()
            row = dict(rows[0], module=key)
            writer.writerow(row)
            if key:
                writer.writerow(row)
            after.write_text(stream.getvalue())
            result = tool.compare(before, after, max_added=100, max_removed=100,
                                  max_changed=100, allow_change=['path'])
            self.assertFalse(result['accepted'])
            self.assertIn('ambiguous_keys' if key else 'empty_module_key',
                          [v['rule'] for v in result['violations']])

    def test_inert_html_includes_policy_and_all_changed_values(self):
        before, _ = self.snapshot('before.csv')
        rows = list(csv.DictReader(io.StringIO(before.read_text())))
        rows[0]['path'] = '</pre><script>bad()</script>\x1b[31m'
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fieldnames=tool.drift.FIELDS)
        writer.writeheader(); writer.writerows(rows)
        after = self.root / 'after.csv'; after.write_text(stream.getvalue())
        status, output, error = self.cli(before, after, '--format', 'html')
        self.assertEqual((status, error), (1, ''))
        self.assertIn('Import change policy: REJECTED', output)
        self.assertIn('Content-Security-Policy', output)
        self.assertIn('&lt;script&gt;', output)
        self.assertNotIn('<script>', output)
        self.assertNotIn('\x1b', output)
        self.assertIn('worker.py', output)

    def test_outside_workspace_refused(self):
        before, _ = self.snapshot('before.csv')
        status, output, error = self.cli(Path.cwd().parent / 'not-read.csv', before)
        self.assertEqual((status, output), (2, ''))
        self.assertIn('inside', json.loads(error)['error'])


if __name__ == '__main__':
    unittest.main()
