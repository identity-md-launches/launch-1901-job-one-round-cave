#!/usr/bin/env python3
"""Explain captured Retry-After hints offline; never wait or retry a request."""
import argparse
import datetime as dt
import email.utils
import json
import math
from pathlib import Path
import re
import sys

MAX_BYTES = 262144
UTC = dt.timezone.utc
IMF_DATE = re.compile(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun), [0-9]{2} '
                      r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) '
                      r'[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} GMT')


def timestamp(text):
    if not isinstance(text, str) or len(text) > 64:
        raise ValueError('requires an ISO timestamp with explicit timezone')
    value = dt.datetime.fromisoformat(text[:-1] + '+00:00' if text.endswith('Z') else text)
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('timestamp requires explicit timezone')
    return value.astimezone(UTC)


def http_date(text):
    # Deliberately conservative: obsolete HTTP-date forms are reported unsupported.
    if not IMF_DATE.fullmatch(text):
        raise ValueError('only IMF-fixdate HTTP dates are supported')
    value = email.utils.parsedate_to_datetime(text)
    if value.year < 1601 or email.utils.format_datetime(value, usegmt=True) != text:
        raise ValueError('invalid HTTP date or weekday')
    return value


def load(path):
    root, target = Path.cwd().resolve(), Path(path).resolve()
    if target != root and root not in target.parents:
        raise ValueError('report must be inside the current workspace')
    with target.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('report exceeds 256 KiB')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def constant(text):
        raise ValueError('non-JSON constant')
    def number(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValueError('non-finite JSON number')
        return value
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=constant, parse_float=number)


def interpret(hop, evidence, at=None):
    status = hop.get('status')
    if type(status) is not int or not 100 <= status <= 599:
        raise ValueError('invalid response status')
    context = ('rate_limit_response' if status == 429 else
               'service_unavailable_response' if status == 503 else
               'redirect_response' if status in {301, 302, 303, 307, 308} else 'other_response')
    result = dict(evidence=evidence, status=status, context=context)
    if 'retry_after' not in hop:
        result['outcome'] = 'not_captured'
        return result
    values = hop['retry_after']
    if (not isinstance(values, list) or len(values) > 32
            or any(not isinstance(v, str) or len(v) > 512 for v in values)):
        raise ValueError('retry_after must be at most 32 strings of 512 characters')
    result['header_evidence'] = evidence + '/retry_after'
    if not values:
        result['outcome'] = 'absent'
        return result
    if len(values) != 1:
        result['outcome'] = 'ambiguous_multiple_fields'
        return result
    text = values[0].strip(' \t')
    if re.fullmatch(r'[0-9]+', text):
        if len(text.lstrip('0')) > 20:
            result['outcome'] = 'out_of_range'
            return result
        delay = int(text)
        result.update(form='delay_seconds', delay_seconds=delay)
        not_before = None
    else:
        try:
            not_before = http_date(text)
        except (ValueError, OverflowError, TypeError):
            result['outcome'] = 'invalid_or_unsupported_value'
            return result
        result.update(form='http_date', not_before=not_before.isoformat())
        delay = None
    try:
        received = timestamp(hop.get('headers_received_at'))
    except (ValueError, OverflowError, TypeError):
        result['outcome'] = 'receipt_time_unavailable'
        return result
    reference = at if at is not None else received
    if reference < received:
        result['outcome'] = 'evaluation_precedes_receipt'
        return result
    if delay is not None:
        try:
            not_before = received + dt.timedelta(seconds=delay)
        except OverflowError:
            result['outcome'] = 'out_of_range'
            return result
    difference = not_before - reference
    remaining = max(0, difference.days * 86400 + difference.seconds
                    + bool(difference.microseconds))
    result.update(not_before=not_before.isoformat(), evaluated_at=reference.isoformat(),
                  evaluation_basis='explicit_time' if at is not None else 'header_receipt',
                  remaining_seconds=remaining,
                  outcome='hint_pending' if remaining else 'hint_elapsed')
    if result['form'] == 'http_date' and not_before < received:
        result['date_precedes_receipt'] = True
    return result


def analyze(source, at=None):
    if at is not None:
        at = timestamp(at)
    if not isinstance(source, dict) or type(source.get('ok')) is not bool:
        raise ValueError('requires a saved probe with boolean ok')
    schema, prefix = source.get('schema'), ''
    if schema == 'deadline-sentry/v1':
        probe = source.get('probe')
        if (not isinstance(probe, dict) or probe.get('ok') is not source['ok']
                or 'error' in source):
            raise ValueError('requires a completed consistent watchdog report')
        source, prefix = probe, '/probe'
    elif schema != 'endpoint-sentry/v1':
        raise ValueError('unsupported report schema')
    if source.get('schema') != 'endpoint-sentry/v1':
        raise ValueError('unsupported probe schema')
    hops = source.get('hops')
    if not isinstance(hops, list) or len(hops) > 32 or any(not isinstance(h, dict) for h in hops):
        raise ValueError('requires at most 32 response hops')
    return dict(schema='retry-lens/v1', source_schema=schema, observed_ok=source['ok'],
                responses=[interpret(h, prefix + '/hops/' + str(i), at)
                           for i, h in enumerate(hops)],
                limits=[
                    'Saved header hints only; no network, waiting, scheduling or retries.',
                    'An elapsed hint does not establish health or permission to retry.',
                    'Delay-seconds start at recorded receipt; HTTP dates use the local recorded clock.',
                    'Clock skew and transit/cache age are not corrected or inferred.',
                    'Only IMF-fixdate dates are supported; malformed/obsolete values remain unknown.',
                    'Old reports without retry_after cannot establish header absence.',
                    'Status context alone does not establish the cause or scope of a failure.',
                    'Reports are unauthenticated; only fields relevant to this analysis are validated.'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('report', help='saved Endpoint/Deadline Sentry JSON inside current workspace')
    parser.add_argument('--at', help='explicit ISO time with timezone; default is each header receipt')
    args = parser.parse_args(argv)
    try:
        result = analyze(load(args.report), args.at)
    except (OSError, ValueError, TypeError, OverflowError, RecursionError):
        print(json.dumps(dict(schema='retry-lens/v1', error='Invalid or unsupported saved report')))
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
