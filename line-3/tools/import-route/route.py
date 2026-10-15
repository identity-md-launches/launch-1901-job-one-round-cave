#!/usr/bin/env python3
"""Explain a shortest directed local-import route without executing inspected code."""
import argparse
from collections import deque
import importlib.util
import json
from pathlib import Path
import sys

SCOPE = ('Shortest route in the explicit static local-import graph only. '
         'Unreachable does not prove runtime isolation. Conditional imports, '
         'dynamic loading, implicit package initialization and external imports '
         'are not simulated. Review retained issues, dynamic calls and hashes. '
         'Equal endpoints have a zero-edge route, not evidence of a cycle.')


def load_budget():
    path = Path(__file__).resolve().parents[1] / 'import-budget' / 'budget.py'
    spec = importlib.util.spec_from_file_location('line3_route_budget', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def explain(report, source, target):
    """BFS with sorted neighbors chooses the lexicographically first shortest path."""
    records = {m['module']: m for m in report['modules']}
    for name in (source, target):
        if name not in records:
            raise ValueError('unknown local module: ' + name)
    graph = {name: set() for name in records}
    for edge in report['edges']:
        graph[edge['from']].add(edge['to'])
    parents = {source: None}
    pending = deque([source])
    while pending and target not in parents:
        node = pending.popleft()
        for child in sorted(graph[node]):
            if child not in parents:
                parents[child] = node
                pending.append(child)
    path = []
    if target in parents:
        node = target
        while node is not None:
            path.append(node)
            node = parents[node]
        path.reverse()
    edges = []
    for start, end in zip(path, path[1:]):
        record = records[start]
        sites = [{'path': record['path'], 'line': item['line'], 'target': item['target']}
                 for item in record['imports'] if item.get('resolved') == end]
        if not sites:
            raise ValueError('missing source evidence: ' + start + ' -> ' + end)
        edges.append({'from': start, 'to': end, 'sites': sorted(
            sites, key=lambda s: (s['path'], s['line'], s['target']))})
    return {'source': source, 'target': target, 'reachable': bool(path),
            'distance': len(edges) if path else None, 'import_path': path, 'edges': edges,
            'issues': report['issues'], 'cycles': report['cycles'],
            'dynamic_imports': [{'module': m['module'], 'path': m['path'], 'line': line}
                                for m in report['modules'] for line in m['dynamic_import_lines']],
            'summary': report['summary'], 'scope': SCOPE}


def main(argv=None):
    budget = load_budget()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path, help='explicit import root within current workspace')
    parser.add_argument('source', help='exact dotted source module name')
    parser.add_argument('target', help='exact dotted target module name')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--strict', action='store_true', help='also fail on scan warnings or cycles')
    for name, value in budget.DEFAULTS.items():
        parser.add_argument('--max-' + name.replace('_', '-'), type=int, default=value, dest=name)
    args = parser.parse_args(argv)
    try:
        scan = budget.scan(args.root, {name: getattr(args, name) for name in budget.DEFAULTS})
        result = dict(explain(scan['map'], args.source, args.target), status='complete',
                      inventory=scan['inventory'], limits=scan['limits'], collection_scope=scan['scope'])
    except (OSError, ValueError, RuntimeError, RecursionError) as exc:
        error = exc.evidence if isinstance(exc, budget.BudgetExceeded) else {
            'type': 'scan_error', 'detail': str(exc)}
        if args.json:
            print(json.dumps({'status': 'refused', 'error': error}, indent=2))
        else:
            print('import-route: ' + str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print('Route: ' + (' -> '.join(result['import_path']) if result['reachable']
                          else 'unreachable in this static graph'))
        for edge in result['edges']:
            for site in edge['sites']:
                print(f"  {site['path']}:{site['line']}: {site['target']}")
        print(f"Warnings: {len(result['issues'])} issues, {len(result['dynamic_imports'])} dynamic calls, "
              f"{len(result['cycles'])} cyclic components")
        print(SCOPE)
    warnings = result['issues'] or result['dynamic_imports'] or result['cycles']
    return int(not result['reachable'] or bool(args.strict and warnings))


if __name__ == '__main__':
    sys.exit(main())
