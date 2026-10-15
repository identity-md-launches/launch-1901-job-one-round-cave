import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('gate', Path(__file__).with_name('gate.py'))
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class GateTests(unittest.TestCase):
    def setUp(self):
        root = Path('test/scratch/csv-gate')
        root.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def compare(self, before, after, keys=('id',), **policy):
        a, b = self.root / 'a.csv', self.root / 'b.csv'
        a.write_bytes(before.encode())
        b.write_bytes(after.encode())
        return gate.evaluate(gate.engine.reconcile(a, b, keys), **policy)

    def test_reordered_exact_strings_pass(self):
        r = self.compare('id,v\na,0001\nb,9007199254740993\n',
                         'v,id\n9007199254740993,b\n0001,a\n')
        self.assertTrue(r['accepted'])
        self.assertTrue(r['comparison']['equal'])

    def test_default_blocks_add_remove_and_edit(self):
        r = self.compare('id,v\na,1\nb,2\n', 'id,v\na,2\nc,3\n')
        self.assertFalse(r['accepted'])
        self.assertEqual([v['kind'] for v in r['violations'] if v['rule'] == 'row_limit'],
                         ['added', 'removed', 'changed'])
        self.assertEqual(r['comparison']['changed'][0]['fields']['v'], {'before': '1', 'after': '2'})

    def test_limit_boundary_passes(self):
        r = self.compare('id,v\na,1\nb,2\n', 'id,v\na,2\nc,3\n',
                         max_added=1, max_removed=1, max_changed=1, allow_change=['v'])
        self.assertTrue(r['accepted'])
        self.assertFalse(r['comparison']['equal'])

    def test_one_over_limit_fails(self):
        r = self.compare('id,v\n', 'id,v\na,1\nb,2\n', max_added=1)
        self.assertEqual(r['violations'], [{'rule': 'row_limit', 'kind': 'added', 'actual': 2, 'maximum': 1}])

    def test_allowed_column_does_not_allow_another(self):
        r = self.compare('id,v,owner\na,1,A\n', 'id,v,owner\na,2,B\n',
                         max_changed=1, allow_change=['v'])
        self.assertEqual(r['violations'][0]['columns'], ['owner'])

    def test_multiple_fields_count_as_one_changed_row(self):
        r = self.compare('id,a,b\nx,1,2\n', 'id,a,b\nx,3,4\n',
                         max_changed=1, allow_change=['a', 'b'])
        self.assertTrue(r['accepted'])

    def test_column_allowance_does_not_raise_row_limit(self):
        r = self.compare('id,v\na,1\n', 'id,v\na,2\n', allow_change=['v'])
        self.assertEqual(len(r['violations']), 1)
        self.assertEqual(r['violations'][0]['rule'], 'row_limit')

    def test_schema_change_never_allowed(self):
        r = self.compare('id,v\na,1\n', 'id,w\na,1\n', max_changed=100, allow_change=['v','w'])
        self.assertFalse(r['accepted'])
        self.assertEqual([v['kind'] for v in r['violations']], ['added_columns','removed_columns'])

    def test_duplicate_identical_keys_never_pass(self):
        r = self.compare('id,v\na,1\na,1\n', 'id,v\na,1\na,1\n',
                         max_added=100, max_removed=100, max_changed=100, allow_change=['v'])
        self.assertFalse(r['accepted'])
        self.assertFalse(r['comparison']['complete'])
        self.assertEqual(len(r['comparison']['ambiguous'][0]['before']), 2)

    def test_composite_keys_and_multiline_values(self):
        r = self.compare('id,site,v\nx,a,"one\ntwo"\nx,b,1\n',
                         'id,site,v\nx,a,"one\nthree"\nx,b,1\n',
                         keys=('id','site'), max_changed=1, allow_change=['v'])
        self.assertTrue(r['accepted'])
        self.assertEqual(r['comparison']['changed'][0]['key'], {'id':'x','site':'a'})

    def test_invalid_policy_limits(self):
        r = gate.engine.reconcile(Path(__file__).with_name('demo-before.csv'),
                                  Path(__file__).with_name('demo-before.csv'), ['item'])
        for value in [-1, True, 0.5]:
            with self.assertRaises(ValueError):
                gate.evaluate(r, max_added=value)

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = gate.main(list(argv))
        return status, out.getvalue(), err.getvalue()

    def test_cli_pass_and_refusal(self):
        d = Path(__file__).parent
        args = [str(d/'demo-before.csv'), str(d/'demo-after.csv'), '--key', 'item']
        status, out, err = self.cli(*args)
        self.assertEqual(status, 1)
        self.assertFalse(json.loads(out)['accepted'])
        status, out, err = self.cli(*args, '--max-added', '1', '--max-changed', '1', '--allow-change', 'quantity')
        self.assertEqual(status, 0)
        self.assertTrue(json.loads(out)['accepted'])
        self.assertEqual(err, '')

    def test_invalid_input_has_no_partial_report(self):
        p = self.root/'bad.csv'
        p.write_bytes(b'id,v\na,1,extra\n')
        status, out, err = self.cli(str(p),str(p),'--key','id')
        self.assertEqual(status, 2)
        self.assertEqual(out, '')
        self.assertIn('error', json.loads(err))

    def test_outside_workspace_refused(self):
        with self.assertRaises(gate.engine.InputError):
            gate.engine.reconcile(Path.cwd().parent/'not-read.csv', self.root/'missing.csv', ['id'])

    def test_unknown_allowance_is_inert(self):
        r = self.compare('id,v\na,1\n', 'id,v\na,2\n', max_changed=1, allow_change=['typo'])
        self.assertFalse(r['accepted'])

    def test_quoted_control_values_in_cli_output(self):
        p = self.root/'controls.csv'
        p.write_bytes(b'id,v\na,\x1b[31m\n')
        q = self.root/'baseline.csv'
        q.write_bytes(b'id,v\na,plain\n')
        status, out, err = self.cli(str(q),str(p),'--key','id')
        self.assertEqual(status, 1)
        self.assertNotIn('\x1b', out)
        self.assertIn('\\u001b', out)
        self.assertEqual(json.loads(out)['comparison']['changed'][0]['fields']['v']['after'], '\x1b[31m')


if __name__ == '__main__':
    unittest.main()
