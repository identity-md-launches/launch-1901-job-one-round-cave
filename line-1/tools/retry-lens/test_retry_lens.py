"""Offline regressions: no requests, environment inspection or outside reads."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import retry_lens as lens


def report(values=None, status=503):
    hop = dict(status=status, headers_received_at='2026-10-15T12:00:00.500000+00:00')
    if values is not None:
        hop['retry_after'] = values
    return dict(schema='endpoint-sentry/v1', ok=False, hops=[hop])


def first(source, at=None):
    return lens.analyze(source, at)['responses'][0]


class RetryTests(unittest.TestCase):
    def test_delay_and_exact_fractional_ceiling(self):
        source = report(['60'])
        result = first(source, '2026-10-15T12:00:01.499999Z')
        self.assertEqual(result['remaining_seconds'], 60)
        self.assertEqual(result['not_before'], '2026-10-15T12:01:00.500000+00:00')
        self.assertEqual(result['outcome'], 'hint_pending')
        self.assertEqual(first(source, '2026-10-15T12:01:00.5Z')['remaining_seconds'], 0)
        self.assertEqual(first(source, '2026-10-15T12:01:00.5Z')['outcome'], 'hint_elapsed')

    def test_zero_leading_zeros_and_optional_whitespace(self):
        for text in ['0', '000', ' \t0\t ']:
            self.assertEqual(first(report([text]))['outcome'], 'hint_elapsed')
        self.assertEqual(first(report(['00012']))['delay_seconds'], 12)

    def test_imf_date_absolute_time_and_clock_offset(self):
        source = report(['Thu, 15 Oct 2026 12:01:00 GMT'])
        result = first(source, '2026-10-15T14:00:30+02:00')
        self.assertEqual(result['remaining_seconds'], 30)
        self.assertEqual(result['form'], 'http_date')
        self.assertEqual(result['context'], 'service_unavailable_response')

    def test_past_date_does_not_claim_health(self):
        result = lens.analyze(report(['Thu, 15 Oct 2026 11:59:59 GMT']))
        self.assertFalse(result['observed_ok'])
        self.assertTrue(result['responses'][0]['date_precedes_receipt'])
        self.assertEqual(result['responses'][0]['outcome'], 'hint_elapsed')

    def test_missing_capture_is_not_absent(self):
        self.assertEqual(first(report())['outcome'], 'not_captured')
        self.assertEqual(first(report([]))['outcome'], 'absent')

    def test_duplicates_are_not_selected_or_combined(self):
        result = first(report(['5', '8']))
        self.assertEqual(result['outcome'], 'ambiguous_multiple_fields')
        self.assertNotIn('remaining_seconds', result)

    def test_invalid_unsupported_and_joined_values(self):
        for text in ['-1', '+1', '1.5', '', '５', '1, 2', '1\r\n',
                     'Wed, 15 Oct 2026 12:00:00 GMT',
                     'Thu, 32 Oct 2026 12:00:00 GMT',
                     'Thu, 15 Oct 2026 12:00:00 PST',
                     'Thursday, 15-Oct-26 12:00:00 GMT',
                     'Thu Oct 15 12:00:00 2026']:
            with self.subTest(text=text):
                result = first(report([text]))
                self.assertEqual(result['outcome'], 'invalid_or_unsupported_value')
                self.assertNotIn('remaining_seconds', result)

    def test_huge_values_never_wrap_or_cap_to_a_short_delay(self):
        for text in ['9' * 500, '99999999999999999999']:
            result = first(report([text]))
            self.assertEqual(result['outcome'], 'out_of_range')
            self.assertNotIn('remaining_seconds', result)

    def test_missing_naive_or_invalid_receipt_is_unknown(self):
        for received in [None, 'bad', '2026-10-15T12:00:00', 7]:
            source = report(['12'])
            source['hops'][0]['headers_received_at'] = received
            self.assertEqual(first(source)['outcome'], 'receipt_time_unavailable')

    def test_evaluation_before_receipt_and_bad_explicit_time(self):
        self.assertEqual(first(report(['12']), '2026-10-15T11:00:00Z')['outcome'],
                         'evaluation_precedes_receipt')
        for at in ['bad', '2026-10-15T12:00:00']:
            with self.assertRaises(ValueError):
                first(report(['12']), at)

    def test_context_not_automatic_retry_policy(self):
        for status, expected in [(429, 'rate_limit_response'),
                                 (503, 'service_unavailable_response'),
                                 (302, 'redirect_response'), (304, 'other_response'),
                                 (200, 'other_response'), (500, 'other_response')]:
            self.assertEqual(first(report([], status))['context'], expected)

    def test_completed_wrapper_and_evidence_pointers(self):
        probe = report(['3'])
        wrapper = dict(schema='deadline-sentry/v1', ok=False, probe=probe)
        before = copy.deepcopy(wrapper)
        result = first(wrapper)
        self.assertEqual(result['header_evidence'], '/probe/hops/0/retry_after')
        self.assertEqual(wrapper, before)
        wrapper['ok'] = True
        with self.assertRaises(ValueError):
            lens.analyze(wrapper)
        with self.assertRaises(ValueError):
            lens.analyze(dict(schema='deadline-sentry/v1', ok=False, error={'kind': 'deadline'}))

    def test_each_hop_has_own_receipt_and_empty_probe_is_unknown(self):
        source = report(['5'], 302)
        second = report(['5'], 429)['hops'][0]
        second['headers_received_at'] = '2026-10-15T12:00:02Z'
        source['hops'].append(second)
        results = lens.analyze(source)['responses']
        self.assertNotEqual(results[0]['not_before'], results[1]['not_before'])
        self.assertEqual(lens.analyze(dict(schema='endpoint-sentry/v1', ok=False, hops=[]))['responses'], [])

    def test_bounded_shape_rejections(self):
        bad = [None, {}, dict(schema='endpoint-sentry/v1', ok=0, hops=[])]
        for field, value in [('status', True), ('status', 600), ('retry_after', '12'),
                             ('retry_after', [12]), ('retry_after', ['a' * 513]),
                             ('retry_after', ['1'] * 33)]:
            source = report(['12'])
            source['hops'][0][field] = value
            bad.append(source)
        bad.append(dict(schema='endpoint-sentry/v1', ok=False, hops=[{}] * 33))
        for source in bad:
            with self.subTest(source=source), self.assertRaises(ValueError):
                lens.analyze(source)

    def test_loader_cli_and_strict_json(self):
        scratch = Path('test/scratch/line1-30')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            path = Path(directory) / 'report.json'
            path.write_text(json.dumps(report(['12'])), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(lens.main([str(path)]), 0)
            self.assertEqual(json.loads(output.getvalue())['responses'][0]['remaining_seconds'], 12)
            for raw in ['{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}', 'x' * (lens.MAX_BYTES + 1)]:
                path.write_text(raw, encoding='utf-8')
                with self.assertRaises(ValueError):
                    lens.load(path)
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(lens.main([str(path)]), 2)

    def test_outside_path_refused_before_open(self):
        outside = Path.cwd().parent / 'never-open-this.json'
        with mock.patch('pathlib.Path.open') as opened:
            with self.assertRaises(ValueError):
                lens.load(outside)
            opened.assert_not_called()


if __name__ == '__main__':
    unittest.main()
