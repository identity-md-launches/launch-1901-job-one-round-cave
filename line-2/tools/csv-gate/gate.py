#!/usr/bin/env python3
"""Check exact CSV differences against explicit limits, without changing data."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys


def load_engine():
    path = Path(__file__).resolve().parents[1] / 'csv-reconcile' / 'reconcile.py'
    spec = importlib.util.spec_from_file_location('csv_gate_engine', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


engine = load_engine()


def evaluate(result, max_added=0, max_removed=0, max_changed=0, allow_change=()):
    """Evaluate only reports produced in-process by the exact reconciler."""
    limits = {'added': max_added, 'removed': max_removed, 'changed': max_changed}
    if any(type(n) is not int or n < 0 for n in limits.values()):
        raise ValueError('row limits must be nonnegative integers')
    allowed = sorted(set(allow_change))
    failures = []
    for kind, limit in limits.items():
        actual = result['summary'][kind]
        if actual > limit:
            failures.append({'rule': 'row_limit', 'kind': kind, 'actual': actual, 'maximum': limit})
    for kind, columns in result['schema'].items():
        if columns:
            failures.append({'rule': 'schema_change', 'kind': kind, 'columns': columns})
    if result['ambiguous']:
        failures.append({'rule': 'ambiguous_keys', 'count': len(result['ambiguous'])})
    for row in result['changed']:
        forbidden = sorted(set(row['fields']) - set(allowed))
        if forbidden:
            failures.append({'rule': 'column_change', 'key': row['key'], 'columns': forbidden,
                             'before_record': row['before_record'], 'after_record': row['after_record']})
    return {'format': 'csv-gate/v1', 'accepted': not failures,
            'policy': {'maximum_rows': limits, 'allowed_changed_columns': allowed,
                       'schema_changes_allowed': False, 'ambiguous_keys_allowed': False},
            'violations': failures, 'comparison': result}


def nonnegative(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('expected a nonnegative integer') from exc
    if number < 0:
        raise argparse.ArgumentTypeError('expected a nonnegative integer')
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before')
    parser.add_argument('after')
    parser.add_argument('--key', action='append', required=True)
    parser.add_argument('--max-added', type=nonnegative, default=0)
    parser.add_argument('--max-removed', type=nonnegative, default=0)
    parser.add_argument('--max-changed', type=nonnegative, default=0)
    parser.add_argument('--allow-change', action='append', default=[], metavar='COLUMN')
    args = parser.parse_args(argv)
    try:
        # No report is accepted from a file: compute the differences ourselves.
        result = engine.reconcile(args.before, args.after, args.key)
        report = evaluate(result, args.max_added, args.max_removed, args.max_changed, args.allow_change)
    except (ValueError, OSError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
    return 0 if report['accepted'] else 1


if __name__ == '__main__':
    sys.exit(main())
