"""Nested ABI admission limits; offline, no fixture files or network access."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch

import abi_workbench as abi


def nested(depth, leaf='uint8', value=7):
    param = {'type': leaf}
    for _ in range(depth):
        param = {'type': 'tuple', 'components': [param]}
        value = [value]
    return param, value


class TypeLimitTests(unittest.TestCase):
    def cli(self, command, raw, reference='f', *arguments):
        output, error = io.StringIO(), io.StringIO()
        with patch.object(abi.Path, 'open', return_value=io.BytesIO(raw)), \
                patch('sys.argv', ['abi', command, '--abi', 'test/scratch/schema.json',
                                  '--function', reference, *arguments]), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = abi.main()
        return status, output.getvalue(), error.getvalue()

    def test_exact_depth_static_layout(self):
        param, value = nested(abi.MAX_TUPLE_DEPTH)
        expected = (7).to_bytes(32, 'big')
        self.assertEqual(abi.encode_tuple([param], [value]), expected)
        self.assertEqual(abi.decode_tuple([param], expected, strict=True)[0]['value'], value)
        signature = 'f(' + '(' * abi.MAX_TUPLE_DEPTH + 'uint8' + ')' * abi.MAX_TUPLE_DEPTH + ')'
        self.assertEqual(abi.function_reference(signature), ('f', signature))

    def test_exact_depth_dynamic_layout(self):
        param, value = nested(abi.MAX_TUPLE_DEPTH, 'string', 'x')
        # Each enclosing dynamic tuple has one offset word; so does its string.
        expected = ((32).to_bytes(32, 'big') * (abi.MAX_TUPLE_DEPTH + 1)
                    + (1).to_bytes(32, 'big') + b'x' + bytes(31))
        self.assertEqual(abi.encode_tuple([param], [value]), expected)
        self.assertEqual(abi.decode_tuple([param], expected, strict=True)[0]['value'], value)

    def test_deep_schema_rejected_by_every_recursive_entry_point(self):
        param, value = nested(1200)
        operations = [lambda: abi.canonical(param), lambda: abi.dynamic(param),
                      lambda: abi.head_words(param), lambda: abi.encode_value(param, value),
                      lambda: abi.encode_tuple([param], [value]),
                      lambda: abi.decode_tuple([param], bytes(32)),
                      lambda: abi.input_signature({'name': 'f', 'inputs': [param]})]
        for operation in operations:
            with self.assertRaisesRegex(ValueError, 'nesting exceeds 32'):
                operation()

    def test_one_level_over_limit(self):
        param, _ = nested(abi.MAX_TUPLE_DEPTH + 1)
        with self.assertRaisesRegex(ValueError, 'nesting'):
            abi.canonical(param)
        reference = 'f(' + '(' * (abi.MAX_TUPLE_DEPTH + 1) + 'bool' + ')' * (abi.MAX_TUPLE_DEPTH + 1) + ')'
        with self.assertRaisesRegex(ValueError, 'nesting'):
            abi.function_reference(reference)

    def test_cyclic_python_schema_refused_without_recursion(self):
        param = {'type': 'tuple', 'components': []}
        param['components'].append(param)
        with self.assertRaisesRegex(ValueError, 'nesting'):
            abi.canonical(param)

    def test_shared_subtrees_count_each_occurrence(self):
        param = {'type': 'uint8'}
        for _ in range(12):
            param = {'type': 'tuple', 'components': [param, param]}
        with self.assertRaisesRegex(ValueError, 'parameter nodes'):
            abi.canonical(param)

    def test_exact_default_node_budget(self):
        # Sixteen tuples, each with 255 scalar children: 4096 occurrences.
        params = [{'type': 'tuple', 'components': [{'type': 'uint8'}] * 255}] * 16
        abi.check_type_tree(params)
        with self.assertRaisesRegex(ValueError, 'parameter nodes'):
            abi.check_type_tree(params + [{'type': 'bool'}])

    def test_node_budget_aggregates_root_parameters(self):
        params = [{'type': 'tuple', 'components': [{'type': 'uint8'}]}] * 3
        with patch.object(abi, 'MAX_TYPE_NODES', 5):
            for operation in (lambda: abi.encode_tuple(params, [[7]] * 3),
                              lambda: abi.decode_tuple(params, bytes(96)),
                              lambda: abi.input_signature({'name': 'f', 'inputs': params}),
                              lambda: abi.function_reference('f((uint8),(uint8),(uint8))')):
                with self.assertRaisesRegex(ValueError, 'parameter nodes'):
                    operation()
        with patch.object(abi, 'MAX_TYPE_NODES', 6):
            self.assertEqual(abi.encode_tuple(params, [[7]] * 3), (7).to_bytes(32, 'big') * 3)
            self.assertEqual(abi.function_reference('f((uint8),(uint8),(uint8))')[0], 'f')

    def test_scalar_array_is_one_schema_node(self):
        with patch.object(abi, 'MAX_TYPE_NODES', 1):
            self.assertEqual(abi.encode_tuple([{'type': 'bool[3]'}], [[True, False, True]]),
                             (1).to_bytes(32, 'big') + bytes(32) + (1).to_bytes(32, 'big'))

    def test_nested_parameter_width_matches_reference_limit(self):
        types = ','.join(['uint8'] * abi.MAX_PARAMS)
        self.assertEqual(abi.function_reference('f((' + types + '))')[0], 'f')
        with self.assertRaisesRegex(ValueError, 'parameters'):
            abi.function_reference('f((' + types + ',uint8))')

    def test_nested_field_shapes(self):
        for child in (None, [], {'type': []}, {'type': ''}, {'type': 'uint', 'name': 7}):
            with self.subTest(child=child), self.assertRaises(ValueError):
                abi.canonical({'type': 'tuple', 'components': [child]})

    def test_bad_parameter_containers_are_value_errors(self):
        for params in (None, 7, {}, 'uint8'):
            with self.subTest(params=params), self.assertRaisesRegex(ValueError, 'parameters must be an array'):
                abi.encode_tuple(params, [])

    def test_deep_reference_rejected_before_file_open(self):
        reference = 'f(' + '(' * 1200 + 'uint' + ')' * 1200 + ')'
        with patch.object(abi.Path, 'open') as opened:
            with self.assertRaisesRegex(ValueError, 'nesting'):
                abi.load_function('test/scratch/unused.json', reference)
            opened.assert_not_called()

    def test_direct_reference_budget(self):
        with self.assertRaisesRegex(ValueError, 'at most'):
            abi.canonical_reference_type('(' * 9000)

    def test_cli_selected_nested_schemas_fail_cleanly(self):
        param, _ = nested(abi.MAX_TUPLE_DEPTH + 1)
        for field in ('inputs', 'outputs'):
            raw = json.dumps([{'type': 'function', 'name': 'f', field: [param]}]).encode()
            for command, args in (('encode', ('--args', '[]')),
                                  ('decode', ('--data', '0x')),
                                  ('decode-call', ('--data', '0x'))):
                with self.subTest(field=field, command=command):
                    status, output, error = self.cli(command, raw, 'f', *args)
                    self.assertEqual((status, output), (2, ''))
                    self.assertIn('error: ABI tuple nesting', error)
                    self.assertNotIn('Traceback', error)

    def test_unsupported_sibling_still_does_not_block_selection(self):
        param, _ = nested(abi.MAX_TUPLE_DEPTH + 1)
        raw = json.dumps([{'type': 'function', 'name': 'f', 'inputs': [param]},
                          {'type': 'function', 'name': 'f', 'inputs': [{'type': 'bool'}]}]).encode()
        status, output, error = self.cli('encode', raw, 'f(bool)', '--args', '[true]')
        self.assertEqual((status, error), (0, ''))
        self.assertEqual(json.loads(output)['signature'], 'f(bool)')


if __name__ == '__main__':
    unittest.main()
