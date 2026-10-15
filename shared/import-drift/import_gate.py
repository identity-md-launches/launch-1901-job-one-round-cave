#!/usr/bin/env python3
"""Review import-snapshot changes against explicit row and column limits."""
import argparse
import html
import json
import sys

import drift
import gate
import review

SCOPE = ('Acceptance means only that these saved CSV differences fit the stated '
         'limits. It does not establish source equality, runtime isolation or '
         'absence of scan warnings. Preserve and review each bounded snapshot\'s '
         'JSON evidence, including skipped files, hashes, cycles and issues. '
         'Use stable input files. No patch is applied and nothing is sent.')


def compare(before, after, max_added=0, max_removed=0, max_changed=0, allow_change=()):
    allowed = tuple(allow_change)
    if set(allowed) - (set(drift.FIELDS) - {'module'}):
        raise ValueError('allow-change must name an import snapshot non-key column')
    # Schema validation and a fresh exact reconciliation, never a saved report.
    comparison = drift.compare(before, after)
    result = gate.evaluate(comparison, max_added, max_removed, max_changed, allowed)
    result['format'] = 'import-change-gate/v1'
    result['scope'] = SCOPE
    # Generic CSV permits literal empty keys. They cannot name an import module.
    for side, path in (('before', before), ('after', after)):
        _, groups, _ = drift.reconcile.load_table(path, ('module',))
        if ('',) in groups:
            result['violations'].append({'rule': 'empty_module_key', 'side': side,
                                         'records': [r['record'] for r in groups[('',)]]})
    result['accepted'] = not result['violations']
    return result


def render_html(result):
    verdict = 'ACCEPTED' if result['accepted'] else 'REJECTED'
    notice = ('<section aria-label="Import change policy"><h2>Import change policy: '
              + verdict + '</h2><p>' + html.escape(result['scope']) + '</p>'
              + '<h3>Effective limits</h3>' + review.exact(result['policy'])
              + '<h3>Violations</h3>' + review.exact(result['violations']) + '</section>')
    document = '\n'.join(review.iter_html(result['comparison']))
    return document.replace('<h2>Comparison settings</h2>',
                            notice + '<h2>Comparison settings</h2>', 1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('before', help='saved import-drift/v1 CSV in workspace')
    parser.add_argument('after', help='saved import-drift/v1 CSV in workspace')
    for name in ('added', 'removed', 'changed'):
        parser.add_argument('--max-' + name, type=gate.nonnegative, default=0)
    parser.add_argument('--allow-change', action='append', default=[],
                        choices=sorted(set(drift.FIELDS) - {'module'}))
    parser.add_argument('--format', choices=('json', 'html'), default='json')
    args = parser.parse_args(argv)
    try:
        result = compare(args.before, args.after, args.max_added, args.max_removed,
                         args.max_changed, args.allow_change)
        output = (render_html(result) if args.format == 'html' else
                  json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    except (OSError, ValueError, RecursionError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=True), file=sys.stderr)
        return 2
    print(output)
    return 0 if result['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
