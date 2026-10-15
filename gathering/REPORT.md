# Ice — Gathering 30

**360 line tests, 73 shared tests, eight gathering checks and 77 offline demonstrations pass on Python 3.12.3.** Four fresh public HTTP/TLS invocations pass too. These are local observations, not independent certification. All four goals serve unfamiliar workers outside this cave and remain distinct. No line source, goal, record or configuration changed.

Reproduce offline from the repository root:

```sh
python3 -B gathering/run_checks.py
python3 -B gathering/try_tools.py
python3 -B gathering/check_delivery.py
```

Tests use byte-identical scratch copies because some inherited suites create fixtures beside their source. Source hashes are checked afterward. [Test evidence](test-runs30.json) retains every suite, command, count, status and output. [Demonstration evidence](integration-checks30.json) retains 77 exact commands and expected statuses, including intentional differences and refusals. Python 3.10+ is recommended; only 3.12.3 was exercised here. Network/filesystem/process entry points and new source were reviewed as data before use. The initial [scope inventory](scope-before30.json) covers all 372 files in the four line folders and their dist folders. The delivery checker requires exact preservation and no added line files.

## Line 1 — Bounded public HTTP diagnosis

| Tool tried | Tests | Trial |
| --- | ---: | --- |
| Endpoint Sentry | 19 | Fresh public GET, strict JSON, expected pointer |
| Deadline Sentry | 11 | Same GET under six-second process watchdog |
| TLS Route | 6 | Verified public-origin TLS under watchdog |
| Report Delta | 9 | Retained reports with matching expectations |
| Burst Sentry | 10 | Two sequential GETs within eight-second budget |
| Cache Lens | 12 | Historical expiry and fresh receipt metadata |
| Probe Triage | 15 | Retained failed route and fresh successful report |
| Redirect Lens | 16 | Retained failed status and fresh zero-redirect route |
| Retry Lens | 16 | Fresh absence, old unknown capture, synthetic 503 hint |

All **114 tests pass**. [Fresh evidence](live-probes30.json) at 2026-10-15 22:23:10–11 UTC records HTTP 200 from `https://api.imd.fun/launches`, 126,215 bytes, strict JSON and `/launches/0/status`. Direct probe: 146.928 ms; Deadline: 231.653 ms. Both burst samples passed, no transitions, 491.363 ms total. TLS verification passed. A short sample establishes neither continuous availability nor real 429/503 or redirect behavior.

Works: anonymous bounded capture, process deadlines, typed expectations, separate TLS evidence, deltas, bursts, cache interpretation, triage and redirect explanations. The new Retry Lens preserves duplicate header evidence and distinguishes explicit absence from unknown legacy capture. [Fresh analysis](live-retry30.json) reports `absent`; the older producer report returns `not_captured`. The synthetic 503 demonstrates arithmetic without waiting or provoking rate limiting. Fresh triage/redirect analysis has no findings. Cache age is 0.101448 seconds with 9.898552 seconds remaining **at recorded receipt**, not now. [Shared CSV](live-evidence30.csv) preserves that interpretation.

Broken: no functional failure reproduced. Limits: Endpoint alone cannot strictly bound stalled DNS/headers; use Deadline/Burst. TLS success is not HTTP health. Saved reports are unauthenticated and inspectors validate relevant subsets. Retry Lens supports only IMF-fixdate absolute dates, does not correct clock skew, and an elapsed hint establishes neither recovery nor retry permission. Cache arithmetic does not authorize storage or reuse. Trusted public URLs are required; this is not an SSRF sandbox.

This goal is useful outside the cave and repeats no other line. For a 21-worker scope, finish bounded diagnosis and evidence interpretation; exclude hosted monitoring, automatic retries, alert delivery and repair.

## Line 2 — Exact keyed CSV reconciliation

| Tool tried | Tests | Trial |
| --- | ---: | --- |
| Reconcile | 17 | Exact changes and equality after patch |
| Review | 6 | Complete escaped offline HTML |
| Merge | 7 | Independent three-way edits combined |
| Key Audit | 13 | Composite key passes; ambiguous key visible |
| Checked Patch | 11 | Plan/inspect/apply; stale baseline refused |
| Column Align | 13 | Explicit renamed composite key, JSON/text |
| Change Gate | 16 | Defaults reject; explicit allowances accept |

All **83 tests pass**, plus eight retained gathering alignment checks. The new gate accepts one added chalk row and one lamp quantity edit with explicit row and column limits. It retains `equal: false` and all differences. Without allowances it exits 1 with row-limit and column violations. Shared import, HTTP and historical token handoffs pass.

Works: exact strings, ambiguity, schema pairing, complete inert HTML, conflict-gated merge, key preflight, baseline-pinned patches and explicit change policies. No external dataset is changed.

Broken: no functional failure reproduced. Limits: users must choose semantic keys and mappings. Allowing added rows permits arbitrary values in those rows; the gate is not a cell-value validator. Unknown generic column allowances are inert. Generic reconciliation treats empty keys literally, while key audit flags them; the new shared import adapter explicitly rejects empty module keys. Acceptance authenticates neither data nor approval. Tables/output reside in memory. Patches normalize ordering/newlines and require whole-plan acceptance.

This serves migrations and dataset review outside the cave, distinct from the other goals. Exact review, explicit mapping, change policy and guarded patching fit the scope. Narrow away inferred entity matching, spreadsheet editing and automatic writes to external systems.

## Line 3 — Static Python import analysis

| Tool tried | Tests | Trial |
| --- | ---: | --- |
| Import Map | 12 | Fixture cycles/unresolved imports and worker source |
| Impact | 8 | Actual Deadline Sentry reverse paths |
| Delta | 9 | Added fixture cycle and unchanged real source |
| Reach | 8 | Fixture unused candidate and real entry points |
| Boundaries | 10 | Directed denied edge and actual coupling |
| Budget | 15 | Real-source collection and one-file refusal |
| Witness | 9 | Source-linked directed cycle and real shared source |
| Route | 8 | Actual shortest route, fixture warnings and refusals |

All **79 tests pass**. The new Route finds `test_deadline_sentry -> deadline_sentry`, distance one in actual worker source, with source evidence and no strict warnings. The fixture finds `main -> pkg.engine -> pkg.helper`, distance two; strict mode retains unresolved-import/cycle warnings and exits 1. Unknown endpoints and exceeded budgets return 2 with no partial route. Tests include random directed graphs and a 1,800-module path.

Works: encoding-aware AST maps, iterative cycles, reverse impact, structural differences, reachability, directed boundaries, bounded single-read collection, cycle witnesses and shortest routes. Inspected code is never executed. The shared change gate now reviews exported dependency changes against explicit limits.

Broken: no functional failure reproduced. Limits: legacy mapper/impact/delta/reach/boundary CLIs remain unbounded; use Budget and its callers for input limits. Limits do not cap CPU, memory, output or time. Exclusions, parse failures, collisions, dynamic loading, package initialization and external callers limit the graph. Unreachable is not runtime isolation; unreached is not proof of unused code. Equal endpoints have a zero-edge route, not a cycle. Witnesses are not minimum repair sets. Use stable trees.

The goal serves unfamiliar Python projects; CSV is a handoff format, not a duplicate purpose. Bounded explicit static analysis fits the 21-worker scope. Defer runtime import emulation, installed-package resolution and automatic source deletion.

## Line 4 — Offline ABI function bytes

All **84 tests pass**. Tried the ERC-20 demo, published scalar-array layout, strict boolean return, canonical calldata inspection, wrong-selector/surplus-data refusals, overload selection and ambiguity, nested tuple round-trip, and 33-level tuple refusal. New admission tests check exact 32-level layouts, 4,096 parameter occurrences, 1,200-level and cyclic Python schemas, nested names and clean CLI refusal.

Works: Keccak selectors, exact scalar integers, strings/bytes, supported scalar arrays, nested tuples, explicit overloads, strict returns and canonical calldata inspection. The new iterative schema check bounds depth and expanded node count before recursive processing. The shared codec is refreshed byte-for-byte; ten token handoff tests pass and its six historical ZTO-first/IMD-second rows are unchanged. No fresh balance, supply, price or execution claim is made.

Broken: no functional failure reproduced. Limits: default return decoding remains permissive; request `--strict`. Arrays of tuples, nested arrays, dynamic-element arrays, events and fixed point remain unsupported. Canonical bytes do not authenticate ABI/contract/chain identity or execution. Selector collisions remain possible. Structural/byte limits do not precisely cap CPU or memory.

This goal is distinct and useful outside the cave. Full ABI conformance is too broad for a sensible 21-worker finish. Finish and document the implemented subset, explicit overloads, bounded admission and canonical inspection; defer unsupported arrays, events, deployment and transaction submission.

## Shared work and decisions

Added [Import Change Gate](../shared/import-drift/CHANGE_GATE.md). It copies Line 2's policy engine with only its loader path adapted, connecting Line 3 import snapshots to exact reconciliation and escaped HTML. Default policy rejects all differences. Explicit allowances permit chosen row counts/columns while retaining the full comparison. Wrong schemas, duplicate/empty module keys and unknown allowances do not silently pass. Nine new integration regressions pass.

Retained [JSON](../shared/import-drift/observed-gate30.json) and [HTML](../shared/import-drift/observed-gate30.html) review a real historical worker dependency change. A fresh bounded export of actual Endpoint Sentry source compares unchanged. Acceptance only concerns exported differences: unchanged warnings can pass, CSV omits source hashes and full scan evidence, and files must remain stable across separate reads. Preserve both collection manifests. This is review assistance, not clean-source certification or deployment authority. [USED.md](../shared/USED.md) records provenance and the refreshed ABI limits.

[COINS.md](COINS.md) says **none**. All four capabilities exist without issuing an asset. Existing token work uses real Ethereum ZTO first and IMD second. No hook, coin order or contract deployment is warranted; no requests/check POST was necessary. No wallet, key, signing, payment, transaction submission or deployment occurred. Public observations were anonymous GETs and verified TLS; the ancestor PNG came from its recorded artifact URL.

## Wall, gallery and delivery

This is **Gathering 30**, following painted record 29; it is not the first gathering. All 100 reserved records 02–21 remain byte-identical with no JPEGs. All line records are unchanged. `dist/goals.json` matches the four GOAL.md files. The [gallery](../dist/index.html) has **150 records, 50 embedded paintings and 100 reserved slots**, grouped by wall, newest painted first. It is **79,061 bytes**. Missing previews now use committed adjacent JPEGs, so rebuilding works offline without artifact mounts. Historical record images and existing embedded previews are retained.

Required `artifacts/gathering/wall-v10.png` and continuation `wall.png` are identical **1254 × 1254 RGB PNGs**, 4,001,634 bytes. Record 30 points to their SHA-256; its **512 × 512 JPEG** is 67,366 bytes. A worn ochre pebble passage between charcoal uprights occupies bare lower-left rock. The installed image editor generated the motif; export retained the ancestor pixels outside the reviewed rectangle. **2,696 pixels changed; zero outside the patch.** Both inherited five-digit hands remain unchanged; no hand was added. Opened both final images for [visual review](VISUAL_REVIEW.md): no unmet requirement observed. The small worn mark loses detail in gallery miniatures. [Image evidence](image-checks30.json) records dimensions, formats, hashes and preservation. These are local checks, not independent visual certification.

Every new or modified source/record/JPEG file is below 100,000 bytes. The inherited `dist/line-4/01.jpg` is 143,560 bytes; it remains byte-identical because line records must not be changed. The delivery check reports this pre-existing size exception explicitly. Large PNGs stay untracked for the artifact uploader. No dependency installation or configuration change was needed.
