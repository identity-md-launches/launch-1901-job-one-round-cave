"""Offline behavioral checks; fixtures stay in the task workspace."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import random
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('route', Path(__file__).with_name('route.py'))
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)
M = R.load_budget().load_mapper()


def mapped(sources):
    return M.inspect(Path('.'), source_bytes={p: s.encode() for p, s in sources.items()})


def graph_report(graph):
    return mapped({n + '.py': ''.join('import ' + t + '\n' for t in sorted(ts))
                   for n, ts in graph.items()})


class RouteTests(unittest.TestCase):
    def test_shortest_tie_direction_and_disconnected(self):
        graph = {'a': {'c', 'b'}, 'b': {'d'}, 'c': {'d'}, 'd': set(), 'e': set()}
        report = graph_report(graph)
        self.assertEqual(R.explain(report, 'a', 'd')['import_path'], ['a', 'b', 'd'])
        self.assertFalse(R.explain(report, 'd', 'a')['reachable'])
        result = R.explain(report, 'a', 'e')
        self.assertIsNone(result['distance'])
        self.assertEqual(result['edges'], [])
        self.assertEqual(result['import_path'], [])
        graph['a'].add('d')
        self.assertEqual(R.explain(graph_report(graph), 'a', 'd')['distance'], 1)

    def test_identity_cycles_and_unknown_module(self):
        report = graph_report({'a': {'b'}, 'b': {'a'}})
        result = R.explain(report, 'a', 'a')
        self.assertEqual(result['import_path'], ['a'])
        self.assertEqual(result['distance'], 0)
        self.assertTrue(result['reachable'])
        self.assertEqual(result['cycles'], [['a', 'b']])
        for source, target in [('absent', 'a'), ('a', 'absent')]:
            with self.assertRaisesRegex(ValueError, 'unknown local module'):
                R.explain(report, source, target)

    def test_relative_import_aliases_and_duplicate_sites(self):
        report = mapped({'pkg/__init__.py': '', 'pkg/a.py':
                         '# comment\nfrom . import b as bee\nfrom . import b\n',
                         'pkg/b.py': 'from .c import thing\n', 'pkg/c.py': ''})
        result = R.explain(report, 'pkg.a', 'pkg.c')
        self.assertEqual(result['import_path'], ['pkg.a', 'pkg.b', 'pkg.c'])
        self.assertEqual([s['line'] for s in result['edges'][0]['sites']], [2, 3])
        self.assertEqual(result['edges'][1]['sites'], [
            {'path': 'pkg/b.py', 'line': 1, 'target': '.c import thing'}])

    def test_warnings_are_retained(self):
        report = mapped({'a.py': 'import b\n__import__("plugin")\n',
                         'b.py': '', 'broken.py': '\x00', 'pkg/__init__.py': '',
                         'pkg.py': ''})
        result = R.explain(report, 'a', 'b')
        self.assertEqual(result['issues'], report['issues'])
        self.assertEqual({i['type'] for i in result['issues']}, {'parse_error', 'module_collision'})
        self.assertEqual(result['dynamic_imports'], [{'module': 'a', 'path': 'a.py', 'line': 2}])

    def test_long_route_is_iterative(self):
        names = [f'n{i:04}' for i in range(1800)]
        report = graph_report({n: {names[i+1]} if i+1 < len(names) else set()
                               for i, n in enumerate(names)})
        result = R.explain(report, names[0], names[-1])
        self.assertEqual(result['import_path'], names)
        self.assertEqual(result['distance'], 1799)

    def test_random_graphs_against_floyd_warshall(self):
        rng = random.Random(30)
        names = list('abcdefg')
        for _ in range(70):
            graph = {n: {t for t in names if rng.random() < .25} for n in names}
            report = graph_report(graph)
            distance = {(a, b): 0 if a == b else 1 if b in graph[a] else 999
                        for a in names for b in names}
            for k in names:
                for a in names:
                    for b in names:
                        distance[a, b] = min(distance[a, b], distance[a, k] + distance[k, b])
            for a in names:
                for b in names:
                    result = R.explain(report, a, b)
                    expected = distance[a, b]
                    self.assertEqual(result['distance'], None if expected == 999 else expected)
                    for x, y in zip(result['import_path'], result['import_path'][1:]):
                        self.assertIn(y, graph[x])
            reversed_report = graph_report(dict(reversed(list(graph.items()))))
            self.assertEqual(R.explain(report, 'a', 'g'), R.explain(reversed_report, 'a', 'g'))

    def test_missing_source_evidence_refused(self):
        report = graph_report({'a': {'b'}, 'b': set()})
        report['modules'][0]['imports'] = []
        with self.assertRaisesRegex(ValueError, 'missing source evidence'):
            R.explain(report, 'a', 'b')

    def test_cli_real_bytes_hashes_refusal_and_no_execution(self):
        scratch = Path('test/scratch'); scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as name:
            root = Path(name)
            marker = root / 'executed'
            source = ('import b\n' + f'open({str(marker)!r}, "w").write("ran")\n').encode()
            (root / 'a.py').write_bytes(source)
            (root / 'b.py').write_text('')
            def cli(*extra, start='a', end='b'):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = R.main([str(root), start, end, '--json', *extra])
                return code, json.loads(out.getvalue())
            code, result = cli('--strict')
            self.assertEqual(code, 0)
            self.assertEqual(result['status'], 'complete')
            self.assertEqual(result['inventory']['manifest'][0]['sha256'], hashlib.sha256(source).hexdigest())
            self.assertEqual(cli(start='b', end='a')[0], 1)
            self.assertEqual(cli(end='missing')[0], 2)
            for options in [('--max-files', '1'), ('--max-total-bytes', '1'), ('--max-depth', '0')]:
                code, result = cli(*options)
                self.assertEqual(code, 2)
                self.assertEqual(result['status'], 'refused')
                self.assertNotIn('import_path', result)
            (root / 'b.py').write_text('__import__("x")\n')
            self.assertEqual(cli()[0], 0)
            self.assertEqual(cli('--strict')[0], 1)
            self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main()
