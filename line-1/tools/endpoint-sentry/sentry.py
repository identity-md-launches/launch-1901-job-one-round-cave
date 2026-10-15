#!/usr/bin/env python3
"""Bounded, anonymous HTTPS GET diagnostics. Python standard library only."""
import argparse
import datetime
import hashlib
import http.client
import json
import math
import socket
import ssl
import sys
import time
import urllib.parse

USER_AGENT = 'Pepeolithic-Endpoint-Sentry/1.0 (public read-only diagnostics)'
REDIRECTS = {301, 302, 303, 307, 308}
# Deliberately omit cookies, authorization and arbitrary response headers.
CACHE_HEADERS = {'cache-control', 'date', 'age', 'expires', 'vary',
                 'etag', 'last-modified'}


def https_url(value):
    """Never accept credentials, fragments, non-HTTPS schemes or header injection."""
    if any(ord(c) <= 32 or ord(c) == 127 for c in value):
        raise ValueError('URL contains whitespace or control characters')
    u = urllib.parse.urlsplit(value)
    if u.scheme != 'https' or not u.hostname or u.username is not None or u.password is not None:
        raise ValueError('URL must be absolute HTTPS without credentials')
    if u.fragment:
        raise ValueError('URL fragments are not sent to servers; remove the fragment')
    port = 443 if u.port is None else u.port
    if not 1 <= port <= 65535:
        raise ValueError('invalid port')
    # ASCII URLs keep both reports and HTTP request targets unambiguous.
    value.encode('ascii')
    return u


def pointer(document, path):
    """Resolve an RFC 6901 JSON pointer, including escaped keys and array indices."""
    if path == '':
        return document
    if not path.startswith('/'):
        raise ValueError('JSON pointer must be empty or start with /')
    for token in path[1:].split('/'):
        for i, char in enumerate(token):
            if char == '~' and (i + 1 == len(token) or token[i + 1] not in '01'):
                raise ValueError('invalid JSON pointer escape')
        key = token.replace('~1', '/').replace('~0', '~')
        if isinstance(document, dict):
            document = document[key]
        elif isinstance(document, list):
            if not key.isascii() or not key.isdecimal() or (len(key) > 1 and key[0] == '0'):
                raise ValueError('invalid array index')
            document = document[int(key)]
        else:
            raise ValueError('pointer crosses a scalar')
    return document


def strict_json(body):
    def invalid(value):
        raise ValueError('non-JSON numeric constant: ' + value)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    def finite_float(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValueError('JSON number exceeds finite float range')
        return value
    # utf-8-sig tolerates a UTF-8 BOM; other encodings are deliberately unsupported.
    return json.loads(body.decode('utf-8-sig'), parse_constant=invalid,
                      parse_float=finite_float, object_pairs_hook=unique)


def json_equal(a, b):
    # Python considers True == 1; JSON expectations must distinguish them.
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(json_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(json_equal(a[k], b[k]) for k in a)
    return a == b


def probe(url, timeout=10.0, max_bytes=1048576, max_redirects=3,
          expected_status=200, expect_json=False, expect_path=None,
          expect_value=None, compare_value=False, connection_factory=None):
    https_url(url)
    start = time.monotonic()
    deadline = start + timeout
    report = {'schema': 'endpoint-sentry/v1', 'url': url,
              'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'ok': False, 'hops': [], 'checks': [], 'limits': {
                  'timeout_seconds': timeout, 'max_bytes': max_bytes,
                  'max_redirects': max_redirects}}
    factory = connection_factory or http.client.HTTPSConnection
    current, visited = url, set()
    stage = 'connect'
    try:
        for hop_number in range(max_redirects + 1):
            if current in visited:
                raise ValueError('redirect loop')
            visited.add(current)
            u = https_url(current)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('probe deadline expired')
            connection = factory(u.hostname, 443 if u.port is None else u.port, timeout=remaining,
                                 context=ssl.create_default_context())
            hop_start = time.monotonic()
            try:
                stage = 'connect'
                connection.connect()
                stage = 'headers'
                target = urllib.parse.urlunsplit(('', '', u.path or '/', u.query, ''))
                request_sent_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                connection.request('GET', target, headers={
                    'User-Agent': USER_AGENT, 'Accept': 'application/json, */*;q=0.1',
                    'Accept-Encoding': 'identity', 'Connection': 'close'})
                response = connection.getresponse()
                received_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                hop = {'url': current, 'status': response.status,
                       'request_sent_at': request_sent_at,
                       'headers_received_at': received_at,
                       'retry_after': [value for key, value in response.getheaders()
                                       if key.lower() == 'retry-after'],
                       'cache_headers': [[key.lower(), value] for key, value in response.getheaders()
                                         if key.lower() in CACHE_HEADERS],
                       'headers_ms': round((time.monotonic() - hop_start) * 1000, 3),
                       'content_type': response.getheader('Content-Type', ''),
                       'content_encoding': response.getheader('Content-Encoding', 'identity')}
                report['hops'].append(hop)
                if response.status in REDIRECTS:
                    location = response.getheader('Location')
                    if not location:
                        raise ValueError('redirect has no Location header')
                    if hop_number == max_redirects:
                        raise ValueError('redirect limit reached')
                    next_url = urllib.parse.urljoin(current, location)
                    https_url(next_url)
                    hop['location'] = next_url
                    current = next_url
                    continue
                stage = 'body'
                if hop['content_encoding'].lower() not in ('', 'identity'):
                    raise ValueError('compressed response refused; requested identity encoding')
                chunks, size = [], 0
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError('probe deadline expired')
                    if connection.sock is not None:
                        connection.sock.settimeout(remaining)
                    chunk = response.read1(min(65536, max_bytes + 1 - size))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    size += len(chunk)
                    hop['body_bytes'] = size
                    if size > max_bytes:
                        hop['body_truncated'] = True
                        raise ValueError('response exceeds byte limit')
                body = b''.join(chunks)
                hop['body_bytes'] = size
                hop['body_sha256'] = hashlib.sha256(body).hexdigest()
                length = response.getheader('Content-Length')
                if length is not None and int(length) != size:
                    raise ValueError('body length differs from Content-Length')
                report['final_url'] = current
                report['checks'].append({'name': 'status', 'ok': response.status == expected_status,
                                         'expected': expected_status, 'actual': response.status})
                if expect_json or expect_path is not None or compare_value:
                    stage = 'json'
                    doc = strict_json(body)
                    report['checks'].append({'name': 'json', 'ok': True})
                    if expect_path is not None:
                        stage = 'json_pointer'
                        actual = pointer(doc, expect_path)
                        report['checks'].append({'name': 'json_pointer', 'path': expect_path, 'ok': True})
                        if compare_value:
                            report['checks'].append({'name': 'json_value', 'path': expect_path,
                                                     'ok': json_equal(actual, expect_value)})
                report['ok'] = all(check['ok'] for check in report['checks'])
                break
            finally:
                connection.close()
    except (OSError, ValueError, KeyError, IndexError, UnicodeError,
            http.client.HTTPException, RecursionError) as error:
        if isinstance(error, ssl.SSLError):
            kind = 'tls'
        elif isinstance(error, socket.gaierror):
            kind = 'dns'
        elif isinstance(error, TimeoutError):
            kind = 'timeout'
        else:
            kind = stage
        report['error'] = {'kind': kind, 'message': str(error)}
    report['elapsed_ms'] = round((time.monotonic() - start) * 1000, 3)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', help='public HTTPS endpoint, without credentials')
    parser.add_argument('--timeout', type=float, default=10, help='time budget in seconds (default 10)')
    parser.add_argument('--max-bytes', type=int, default=1048576)
    parser.add_argument('--max-redirects', type=int, default=3)
    parser.add_argument('--status', type=int, default=200)
    parser.add_argument('--json', action='store_true', help='require a valid UTF-8 JSON response')
    parser.add_argument('--expect-path', help='require this RFC 6901 pointer to exist; empty string is root')
    parser.add_argument('--expect-value', help='JSON value to compare at --expect-path')
    args = parser.parse_args(argv)
    try:
        https_url(args.url)
        if not math.isfinite(args.timeout) or not 0 < args.timeout <= 120:
            raise ValueError('timeout must be greater than 0 and at most 120 seconds')
        if not 1 <= args.max_bytes <= 16777216:
            raise ValueError('max-bytes must be between 1 and 16777216')
        if not 0 <= args.max_redirects <= 10:
            raise ValueError('max-redirects must be between 0 and 10')
        if not 100 <= args.status <= 599:
            raise ValueError('status must be between 100 and 599')
        if args.expect_value is not None and args.expect_path is None:
            raise ValueError('--expect-value requires --expect-path')
        value = strict_json(args.expect_value.encode()) if args.expect_value is not None else None
        if args.expect_path is not None:
            # Syntax is validated even when the server is unreachable.
            for token in args.expect_path.split('/')[1:]:
                pointer({token.replace('~1', '/').replace('~0', '~'): None}, '/' + token)
            if args.expect_path and not args.expect_path.startswith('/'):
                raise ValueError('JSON pointer must be empty or start with /')
    except (ValueError, UnicodeError) as error:
        parser.error(str(error))
    result = probe(args.url, args.timeout, args.max_bytes, args.max_redirects,
                   args.status, args.json, args.expect_path, value, args.expect_value is not None)
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
