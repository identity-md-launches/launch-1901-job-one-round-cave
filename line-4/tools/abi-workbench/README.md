# ABI Workbench

A Python standard-library CLI that computes Ethereum selectors with Keccak-256,
encodes unsigned function calldata, and decodes supplied return bytes offline.
It never connects to RPC, signs, sends, pays, or reads keys or environment values.
ABI paths are explicit inputs; keep them inside your workspace.

## Run it

From the repository root:

```sh
python3 -B -m unittest discover -s line-4/tools/abi-workbench -v
```

This runs 84 regression tests, including the gathering's defect reports,
all 32 integer widths, malformed output checks, and eight Keccak vectors
independently obtained using `cast keccak` (Cast is not needed to run the tests).
All 84 passed locally, including input-boundary, scalar-array, strict-return,
calldata-inspection, explicit-overload and nested-type admission tests. The original demo also passed:

```sh
python3 -B line-4/tools/abi-workbench/abi_workbench.py --demo
```

The demo's transfer **argument** is the real ZTO address; it is only a formatting
example, not a destination envelope or an executed token transfer. Its amount is
illustrative, not a balance or price. It prints `0xa9059cbb` and complete calldata.

Pepe 24 added one-dimensional arrays of static scalar types, both fixed
(`uint8[2]`) and dynamic (`uint8[]`). The included `array-example.json`
reproduces the published Solidity ABI example without connecting to a chain:

```sh
python3 -B line-4/tools/abi-workbench/abi_workbench.py encode --abi line-4/tools/abi-workbench/array-example.json --function f --args '[291,[1110,1929],"0x31323334353637383930","0x48656c6c6f2c20776f726c6421"]'
```

Tried locally: this prints selector `0x8be65246` and the calldata bytes from
the [Solidity ABI specification](https://docs.soliditylang.org/en/latest/abi-spec.html#use-of-dynamic-types).
The new tests also check a fixed array followed by a dynamic array using ZTO
and IMD addresses, empty arrays, invalid counts, truncated return arrays, and
invalid element words. The output of `decode` represents arrays as JSON arrays.

An included ABI exercises canonical alias handling:

```sh
python3 -B line-4/tools/abi-workbench/abi_workbench.py encode --abi line-4/tools/abi-workbench/alias-example.json --function transfer --args '["0xd782bdea4ef02a0bd391eb9089470c8080f0a68e",12]'
```

For your ABI use `encode --abi PATH --function NAME --args '[...]'`, or
`decode --abi PATH --function NAME --data 0x...`. Run from your workspace root; resolved ABI paths must stay inside that directory.
ABI files are UTF-8 JSON arrays of entry objects (a UTF-8 BOM is accepted). Integer inputs must be exact JSON integers or decimal strings
(e.g. `"1000000000000000000"`); floats, booleans, exponent strings and whitespace
are rejected. JSON numeric exponents parse as floats and are rejected too.

## Supported scope and repairs

Supports `address`, `bool`, `int`/`uint` (canonicalized to 256 bits), widths
8 through 256 in steps of 8, `bytes1` through `bytes32`, `string`, and `bytes`.
One-dimensional fixed and dynamic arrays of `address`, `bool`, `int`/`uint`
and fixed bytes are supported, with a 4,096-item maximum. Fixed arrays occupy
their full number of head words; dynamic arrays use a length-prefixed tail.
The new repair combines Keccak's padding bits at the 135-byte boundary, avoids
lossy integer conversion, canonicalizes aliases before selector hashing, and
rejects signed words with invalid sign extension. Additional checks reject
nonzero address/bytes padding, dynamic offsets into the head, missing tail
padding, and nonzero dynamic padding. Direct `encode_value` calls now use the
same type validation as the CLI.

Nested tuples are supported, including dynamic tuple fields and tuples that
contain the supported scalar arrays. Arrays of tuples, nested arrays, arrays of
`string` or dynamic `bytes`, events and fixed point remain unsupported.
Ambiguous bare function names are rejected;
explicit signatures can select overloads as described below. The default decoder permits noncanonical tail layouts and surplus words for
compatibility. Use `decode --strict` to require exact canonical re-encoding for
the supported types; unsupported ABI types remain unsupported. ABI files are limited to 1 MiB before parsing. Argument JSON and ABI byte budgets are documented below. This is a
local byte interpreter, not proof of an on-chain value or transaction success.
The tests are regressions, not an independent audit or full ABI conformance suite.

## Checked inputs (Pepe 23)

The gathering's malformed-object ABI and missing-file reproductions now return
exit 2 with a concise `error:` on stderr and no success output or traceback.
The reader checks the ABI container, entry kinds/names, input/output arrays,
parameter objects, type strings and optional parameter names. Unsupported types
in the selected function's inputs and outputs fail explicitly; unrelated valid
entries can contain types the workbench does not implement. This is structural
validation for this interpreter, not complete Solidity ABI schema validation.

Malformed JSON/UTF-8, duplicate JSON fields, excessive JSON nesting and files
over 1 MiB are rejected. File I/O failures are handled at the CLI boundary.
Paths outside the current workspace, including resolved symlinks, are rejected
before opening. This path check is for trusted local CLI use, not isolation
against concurrent malicious filesystem changes or special files.

At Pepe 23, 23 tests passed; the demo and alias `transfer` example still
produce selector `0xa9059cbb`. Real CLI calls with an object-shaped ABI and a
missing ABI both produced exit 2 and one error line. No RPC was needed for this
repair, and no signing or transaction submission capability was added. Pepe 24's
array extension brings the passing total to 27.


## Strict return decoding (Pepe 25)

Add `--strict` when interpreting bytes from an untrusted source. After normal
value and padding checks, the decoder encodes the decoded values again and
requires byte-for-byte equality. This rejects shared or overlapping dynamic
tails, reordered tails, gaps and unused suffix words. Empty outputs require
empty bytes. The Python API is `decode_tuple(params, data, strict=True)`; the
existing two-argument API and default CLI behavior stay compatible.

One command anyone can run from the repository root:

```sh
python3 -B line-4/tools/abi-workbench/abi_workbench.py decode --abi line-4/tools/abi-workbench/alias-example.json --function transfer --strict --data 0x0000000000000000000000000000000000000000000000000000000000000001
```

Tried locally: exits 0 and prints the boolean output `ok: true`. This is an
offline return-byte fixture, not a transfer, receipt or on-chain observation.
Appending another 32-byte word exits 2 with `error: noncanonical return data`
and no success output. The complete suite passes 36 tests, including nine new
strict-mode regressions with independently laid-out ABI words. They cover mixed
fixed arrays, ZTO's real address, signed values, strings, dynamic arrays, empty
values, padding and CLI success/error behavior.

Strict decoding validates byte layout for the supported type subset; it does
not authenticate the source of those bytes. It holds decoded values and a
second encoded copy in memory. Pepe 27 adds the explicit input and decoded-footprint limits below.

## Calldata inspection (Pepe 26)

`decode-call` reads supplied calldata for one function in a local ABI. It
checks the four-byte selector, decodes the supported arguments, and requires
canonical ABI layout: no gaps, shared tails or extra words. It only interprets
bytes already provided to it. It does not query a chain or send the call.

From the repository root, this one command decodes a known `transfer` byte
fixture containing the real ZTO address and an illustrative amount of 12:

```sh
python3 -B line-4/tools/abi-workbench/abi_workbench.py decode-call --abi line-4/tools/abi-workbench/alias-example.json --function transfer --data 0xa9059cbb000000000000000000000000d782bdea4ef02a0bd391eb9089470c8080f0a68e000000000000000000000000000000000000000000000000000000000000000c
```

Tried locally: exit 0, selector `0xa9059cbb`, recipient
`0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`, amount 12. Six new tests
cover this independently known ERC-20 selector, malformed selectors,
truncation, surplus words and a displaced dynamic tail. The full 42-test suite
passes. A valid selector and canonical bytes do not prove that a transaction
was signed, sent, executed or successful. The supported ABI type subset and
byte budgets below also apply here.


## Bounded inputs and decoded footprints (Pepe 27)

The CLI limits argument JSON to 1 MiB of UTF-8 and 64 nesting levels before
parsing. Duplicate JSON object fields are rejected. Hex input is length-checked
before matching or conversion: at most 1 MiB of return/argument bytes, plus
four selector bytes for calldata. ABI files retain their existing 1 MiB limit.
Tuples contain at most 256 parameters; the existing 4,096-item array limit remains.
The Python tuple APIs enforce the parameter and byte budgets too.

Encoding checks the aggregate ABI head and tails before growing the result.
Decoding charges the head plus every referenced dynamic tail against 1 MiB,
including repeated references in permissive mode, before copying each value.
Thus shared offsets cannot amplify a small physical payload into unlimited
output. This deliberately rejects some previously accepted large/noncanonical
inputs. Strict canonical checks remain unchanged within those budgets.
These are data-size limits, not a precise process-memory or execution-time cap:
Python objects, parsed JSON and formatted output add overhead, and caller-owned
inputs already exist before these functions receive them.

One command from the repository root exercises the new boundaries:

```sh
python3 -B -m unittest discover -s line-4/tools/abi-workbench -p test_budgets.py -v
```

Tried locally: all eight budget tests passed, and all 50 workbench tests passed.
Checks include exact boundaries, UTF-8 byte counts, excessive JSON nesting,
aggregate encoding, alias amplification and CLI rejection with exit 2 and no
success output. The original ZTO transfer demo still runs offline. Nothing is
signed, sent or queried on chain, and no dependency was added.

## Explicit overloaded functions (Pepe 28)

Workers can now select overloaded functions with a full `--function` signature
in all three commands: `encode`, `decode`, and `decode-call`. A bare name still
requires exactly one function entry. The tool never guesses from argument
values, return data, or a four-byte selector. This matters when two overloads
accept the same JSON value but encode it differently.

One command from the repository root shows it working:

```sh
python3 -B line-4/tools/abi-workbench/abi_workbench.py encode --abi line-4/tools/abi-workbench/overload-example.json --function 'bar(bytes3[2])' --args '[["0x616263","0x646566"]]'
```

Tried locally: exit 0, selector `0xfce353f6`, followed by the exact two words
in the [Solidity ABI specification's bar example](https://docs.soliditylang.org/en/latest/abi-spec.html#examples).
The fixture adds illustrative overloads to the published `bar` and `baz`
functions; it is an offline ABI fixture, not the ABI of an identified deployed
contract. Replacing the signature with bare `bar` returns exit 2, an ambiguity
error, and no success output. Nothing is sent to any contract.

Quote signatures in a shell. Spaces, parameter names, return types,
unsupported types and malformed signatures are rejected. `uint` and `int`
aliases normalize to 256 bits in both the supplied reference and the ABI,
including supported arrays. For example, `bar(uint)` selects `bar(uint256)`.
Zero-argument signatures such as `symbol()` work too. Function references
are limited to 8,192 characters and 256 input types. ABI/data budgets and the
supported type subset remain in force.

Selection compares the complete canonical input signature, not its four-byte
hash. Duplicate canonical signatures are refused, even if parameter names or
output types differ. An unsupported sibling overload does not prevent selecting
a supported overload; unsupported inputs or outputs of the selected function
still fail. This does not add event support or authenticate an ABI, contract,
chain, or execution result. Selector collisions can exist; choosing
an explicit signature does not prove which function a contract implements.

All 68 tests passed locally, including 12 overload regressions and six tuple
tests. The overload checks cover published calldata, all three CLI commands,
alias equivalence, duplicate signatures, unsupported siblings, empty inputs,
arrays, bounded references, and concise error exits without success output.
Tuple tests cover static and dynamic layouts, nested values, malformed offsets,
explicit signatures and CLI behavior. The tool still uses only Python's
standard library and works with no network or installed dependency.

## Nested tuples (Pepe 29)

The encoder and decoder now accept ABI `tuple` parameters with a `components`
array in an ABI JSON file. Nested tuple components, static tuples inline in a
head, dynamic tuple tails, and tuples containing previously supported scalar
arrays are encoded and decoded recursively. Tuple values use nested JSON arrays
in component order. Explicit function references can name tuple signatures;
for example `put((uint256,string))`. Strict return decoding and canonical
calldata inspection re-encode the complete tuple tree before accepting bytes.

From the repository root, this command encodes a tuple containing an integer
and a dynamic string:

```sh
python3 -B line-4/tools/abi-workbench/abi_workbench.py encode --abi line-4/tools/abi-workbench/tuple-example.json --function 'put((uint256,string))' --args '[[7,"hi"]]'
```

Tried locally: exit 0, selector `0x58b31d65`, and calldata beginning with the
outer tuple offset `0x20`; inside the tuple the string offset is `0x40`. The
six new standard-library tests check that layout, inline static tuples, nested
tuple and array values, malformed offsets, explicit signatures, and CLI
round-trips. Array-of-tuple inputs and nested arrays are still unsupported.
No chain connection or dependency is needed.

## Bounded tuple schemas (Pepe 30)

Nested tuples now have explicit admission limits before recursive encoding,
decoding or canonicalization. Previously, a deeply nested type or function
reference could raise an uncaught `RecursionError`, and a nested component's
non-string `name` escaped the top-level parameter validation.

Each input or output parameter tree is limited to 32 nested tuple levels and
4,096 parameter occurrences in total. A tuple counts as one occurrence, as
does a scalar or scalar-array parameter; array values retain their separate
4,096-item limit. The outer function parameter list is not a tuple level.
Every tuple still has 1 through 256 components. Reusing a Python dictionary
in multiple places counts each occurrence because its representation expands
each time. Cyclic Python schemas are refused by the depth limit.

An iterative pass checks the schema before recursive type processing. Nested
names, when present, must be strings. Explicit signatures enforce the same
tuple depth, component width and aggregate node budgets, as well as the
existing 8,192-character reference limit. Unsupported sibling overloads still
do not block explicit selection of a supported signature. Selected inputs and
outputs are checked separately; the complete ABI is not required to use only
the supported type subset.

One command from the repository root demonstrates the new boundaries offline:

```sh
python3 -B -m unittest discover -s line-4/tools/abi-workbench -p test_type_limits.py -v
```

Tried locally: all 16 checks pass. They include independently constructed
32-level static and dynamic byte layouts, the exact 4,096-node boundary,
1,200-level refusals, shared and cyclic schemas, nested name validation,
signature admission before opening an ABI file, and clean failures for all
three CLI commands. Refused CLI inputs exit 2, print a concise error to stderr,
and emit no success JSON. All 84 tests and the original ZTO demo pass.

These limits deliberately refuse deeper or larger schemas even if an ABI
implementation with different limits could handle them. They are structural
limits, not a process-memory or elapsed-time guarantee. Existing byte budgets,
strict decoding options, unsupported types and offline-only behavior remain
in effect. No dependency was added.
