"""Offline transport fixtures; no network, credentials or external dependencies."""
import contextlib
import io
import json
import socket
import ssl
import unittest
from unittest import mock
import sentry


class Response:
    def __init__(self, status=200, body=b'{}', headers=None):
        self.status, self.body = status, io.BytesIO(body)
        self.headers = headers or {}
    def getheader(self, name, default=None):
        return self.headers.get(name, default)
    def getheaders(self):
        return list(self.headers.items())
    def read1(self, amount):
        return self.body.read(amount)


class Transport:
    def __init__(self, responses):
        self.responses, self.calls, self.closed = iter(responses), [], 0
    def __call__(self, host, port, **kwargs):
        owner = self
        class Connection:
            sock = None
            def connect(self):
                pass
            def request(self, method, target, headers):
                owner.calls.append((host, port, method, target, headers))
            def getresponse(self):
                response = next(owner.responses)
                if isinstance(response, BaseException):
                    raise response
                return response
            def close(self):
                owner.closed += 1
        return Connection()


class SentryTests(unittest.TestCase):
    def run_probe(self, responses, **kwargs):
        self.transport = Transport(responses)
        return sentry.probe('https://example.com/start', connection_factory=self.transport, **kwargs)

    def test_json_expectation_and_no_authorization(self):
        r = self.run_probe([Response(body=b'{"items":[{"ok":true}]}')],
                           expect_path='/items/0/ok', expect_value=True, compare_value=True)
        self.assertTrue(r['ok'])
        self.assertEqual(self.transport.closed, 1)
        call = self.transport.calls[0]
        self.assertEqual(call[2:4], ('GET', '/start'))
        self.assertEqual(call[4]['User-Agent'], sentry.USER_AGENT)
        self.assertNotIn('Authorization', call[4])
        self.assertNotIn('Cookie', call[4])

    def test_cache_evidence_is_allowlisted_and_timed(self):
        r = self.run_probe([Response(headers={'Cache-Control': 'max-age=60',
                                              'Set-Cookie': 'private',
                                              'X-Private': 'omit'})])
        hop = r['hops'][0]
        self.assertEqual(hop['cache_headers'], [['cache-control', 'max-age=60']])
        self.assertLessEqual(hop['request_sent_at'], hop['headers_received_at'])
        self.assertNotIn('private', json.dumps(r))

    def test_status_mismatch_is_actionable(self):
        r = self.run_probe([Response(503)])
        self.assertFalse(r['ok'])
        self.assertEqual(r['checks'][0]['actual'], 503)

    def test_retry_after_capture_distinguishes_absent_and_duplicates(self):
        r = self.run_probe([Response(429, headers={'Retry-After': '12',
                                                 'Set-Cookie': 'private'})])
        self.assertEqual(r['hops'][0]['retry_after'], ['12'])
        self.assertFalse(r['ok'])
        self.assertNotIn('private', json.dumps(r))
        self.assertEqual(self.run_probe([Response()])['hops'][0]['retry_after'], [])
        response = Response(503)
        response.getheaders = lambda: [('Retry-After', '5'), ('retry-after', '8')]
        r = self.run_probe([response])
        self.assertEqual(r['hops'][0]['retry_after'], ['5', '8'])

    def test_relative_redirect_and_limit(self):
        r = self.run_probe([Response(302, headers={'Location': '/next'}), Response()])
        self.assertTrue(r['ok'])
        self.assertEqual(r['final_url'], 'https://example.com/next')
        self.assertEqual(self.transport.closed, 2)
        r = self.run_probe([Response(302, headers={'Location': '/next'})], max_redirects=0)
        self.assertFalse(r['ok'])
        self.assertIn('redirect limit', r['error']['message'])

    def test_redirect_loop_and_downgrade(self):
        for location, message in [('/start', 'loop'), ('http://example.com/', 'HTTPS'),
                                   ('https://user:password@example.com/', 'credentials')]:
            with self.subTest(location=location):
                r = self.run_probe([Response(302, headers={'Location': location})])
                self.assertFalse(r['ok'])
                self.assertIn(message, r['error']['message'])
                self.assertEqual(len(self.transport.calls), 1)

    def test_body_limit_and_exact_limit(self):
        self.assertTrue(self.run_probe([Response(body=b'1234')], max_bytes=4)['ok'])
        r = self.run_probe([Response(body=b'12345')], max_bytes=4)
        self.assertFalse(r['ok'])
        self.assertIn('byte limit', r['error']['message'])

    def test_truncation_and_compression(self):
        for response in [Response(body=b'{}', headers={'Content-Length': '5'}),
                         Response(headers={'Content-Encoding': 'gzip'})]:
            self.assertFalse(self.run_probe([response])['ok'])

    def test_strict_json(self):
        for body in [b'{', b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b'\xff']:
            with self.subTest(body=body):
                r = self.run_probe([Response(body=body)], expect_json=True)
                self.assertFalse(r['ok'])
                self.assertEqual(r['error']['kind'], 'json')

    def test_missing_path_and_type_mismatch(self):
        r = self.run_probe([Response()], expect_path='/absent')
        self.assertFalse(r['ok'])
        self.assertEqual(r['error']['kind'], 'json_pointer')
        r = self.run_probe([Response(body=b'{"n":true}')], expect_path='/n',
                           expect_value=1, compare_value=True)
        self.assertFalse(r['ok'])
        self.assertFalse(r['checks'][-1]['ok'])

    def test_pointer_escapes_and_root(self):
        doc = {'a/b': {'~': [7]}, '': 9}
        self.assertEqual(sentry.pointer(doc, '/a~1b/~0/0'), 7)
        self.assertEqual(sentry.pointer(doc, '/'), 9)
        self.assertIs(sentry.pointer(doc, ''), doc)
        for path in ['/a~2b', '/a~1b/~0/00', '/a~1b/~0/-1']:
            with self.assertRaises(ValueError):
                sentry.pointer(doc, path)

    def test_network_error_categories(self):
        for error, kind in [(socket.gaierror('no host'), 'dns'),
                            (TimeoutError('too slow'), 'timeout'),
                            (ssl.SSLError('bad certificate'), 'tls')]:
            r = self.run_probe([error])
            self.assertFalse(r['ok'])
            self.assertEqual(r['error']['kind'], kind)
            self.assertEqual(self.transport.closed, 1)

    def test_url_rejections(self):
        for url in ['http://example.com', 'https://u:p@example.com',
                    'https://example.com/#x', 'https://example.com/\nX: hi',
                    'https://example.com:99999', 'https://example.com/é']:
            with self.assertRaises((ValueError, UnicodeError)):
                sentry.https_url(url)

    def test_explicit_zero_port_rejected_before_connection(self):
        for url in ['https://example.com:0/', 'https://example.com:000/',
                    'https://[2001:db8::1]:0/']:
            with self.subTest(url=url):
                transport = mock.Mock()
                with self.assertRaisesRegex(ValueError, 'invalid port'):
                    sentry.probe(url, connection_factory=transport)
                transport.assert_not_called()

    def test_default_and_explicit_ports_reach_requested_destination(self):
        for suffix, expected in [('', 443), (':443', 443), (':1', 1),
                                 (':8443', 8443), (':65535', 65535)]:
            with self.subTest(port=suffix):
                transport = Transport([Response()])
                r = sentry.probe('https://example.com' + suffix + '/health',
                                 connection_factory=transport)
                self.assertTrue(r['ok'])
                self.assertEqual(transport.calls[0][:4],
                                 ('example.com', expected, 'GET', '/health'))

    def test_redirect_zero_port_refused_before_second_connection(self):
        for location in ['https://example.com:0/next', '//other.example:000/next']:
            with self.subTest(location=location):
                transport = Transport([Response(302, headers={'Location': location})])
                factory = mock.Mock(side_effect=transport)
                r = sentry.probe('https://example.com/start', connection_factory=factory)
                self.assertFalse(r['ok'])
                self.assertIn('invalid port', r['error']['message'])
                self.assertEqual(factory.call_count, 1)
                self.assertEqual(transport.closed, 1)
                self.assertNotIn('final_url', r)

    def test_redirect_explicit_valid_port_preserved(self):
        r = self.run_probe([Response(302, headers={
            'Location': 'https://other.example:8443/next'}), Response()])
        self.assertTrue(r['ok'])
        self.assertEqual(self.transport.calls[1][:4],
                         ('other.example', 8443, 'GET', '/next'))

    def test_cli_zero_port_is_argument_error_without_network(self):
        errors = io.StringIO()
        with mock.patch.object(sentry.http.client, 'HTTPSConnection') as connection:
            with contextlib.redirect_stderr(errors), self.assertRaises(SystemExit) as caught:
                sentry.main(['https://example.com:0/'])
            self.assertEqual(caught.exception.code, 2)
            self.assertIn('invalid port', errors.getvalue())
            connection.assert_not_called()

    def test_cli_validation(self):
        for flags in [['--timeout', 'nan'], ['--max-bytes', '0'],
                      ['--max-redirects', '-1'], ['--expect-value', 'true'],
                      ['--expect-path', '/broken~'], ['--expect-path', 'broken']]:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                sentry.main(['https://example.com'] + flags)
            self.assertEqual(caught.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
