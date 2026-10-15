# Import Change Gate

Review a proposed change to Python import snapshots against explicit limits,
with every exact difference kept in JSON or an offline HTML page. This joins
Line 3's import CSV exports with Line 2's new CSV Change Gate and existing
escaped HTML review. Python 3.10+ standard library only; no installation.

From the repository root, this command checks a real retained worker-source
change: one test module gained an external import.

```sh
python3 -B shared/import-drift/import_gate.py shared/import-drift/observed-sentry.csv shared/import-drift/observed-sentry23.csv --max-changed 1 --allow-change external_imports
```

Observed: exit **0**, `accepted: true`, one changed module (`test_sentry`),
one unchanged module and no ambiguity. The complete comparison remains
`equal: false`. Remove the two allowance options and it returns **1**, with
both a changed-row limit violation and the forbidden column change. Add
`--format html` for a self-contained, script-free review. Retained results:
[JSON](observed-gate30.json) and [HTML](observed-gate30.html).

For new source snapshots, prefer `bounded_snapshot.py ROOT` over the legacy
unbounded `drift.py snapshot`. Save stdout as CSV and stderr as its JSON evidence.
Exit 1 means a completed snapshot has warnings; exit 2 means refused collection
and emits no CSV. Never discard or treat a refusal's empty stdout as a snapshot.
Example workflow, with all temporary files inside this workspace:

```sh
mkdir -p test/scratch/import-review
python3 -B shared/import-drift/bounded_snapshot.py line-1/tools/endpoint-sentry > test/scratch/import-review/before.csv 2> test/scratch/import-review/before.json
python3 -B shared/import-drift/bounded_snapshot.py line-1/tools/endpoint-sentry > test/scratch/import-review/after.csv 2> test/scratch/import-review/after.json
python3 -B shared/import-drift/import_gate.py test/scratch/import-review/before.csv test/scratch/import-review/after.csv
```

Tried on the actual current Endpoint Sentry source: two unchanged modules,
one local edge, no collection warnings; default policy accepts. This proves
only equal exported import fields, not equal source bytes or behavior.

## Policy and boundaries

The key is always `module`. Input columns must exactly match the import-drift
schema; unknown schemas return **2**, with no partial review. The adapter
rejects duplicate and empty module keys, permits valid header-only exports,
and rejects unknown column allowances. `--max-added`, `--max-removed` and
`--max-changed` default to zero and count rows. A changed row must satisfy both
the row limit and every changed-column allowance. Repeat `--allow-change` to
name multiple fields. Additions and removals are governed by their row limits;
allowing them permits whole rows with arbitrary values, so review those rows.

Exit **0** means differences fit the supplied policy, **1** means computed but
rejected, **2** means invalid input or I/O failure. The adapter recomputes the
comparison from the CSV inputs; it never trusts an imported comparison report.
It prints only, changes neither input, applies no patch and performs no network
or environment access. Keep the entire `shared/import-drift/` folder together
when reusing it; all dependencies are ordinary Python source files here.

Acceptance is **not a clean-source verdict**. An unchanged parse warning may
pass a zero-change policy. CSV is a structural projection: it omits ordinary
source edits, source hashes, full cycle evidence and collection exclusions.
Preserve and review both snapshot JSON manifests separately. CSV list fields
are compared as exact strings, not validated as a complete import-map schema.
This does not infer safe imports, installed packages, runtime reachability,
approval authority or permission to deploy. Use stable files: schema checks,
comparison and key checks read inputs separately, not as an atomic snapshot.
Inherited CSV limits are 16 MiB and 100,000 data records per input. Reports and
inputs are held in memory; output size, CPU and wall time are not capped.

## Checks

```sh
python3 -B -m unittest discover -s shared/import-drift -p test_import_gate.py -v
```

All nine tests passed on Python 3.12.3. They exercise real temporary source
exports without executing them, row limits, column allowances, additions and
removals, unchanged warning semantics, empty exports, wrong schemas, ambiguous
and empty keys, workspace containment, CLI statuses and escaped HTML controls.
The complete shared and line suites also pass; see the gathering report.
