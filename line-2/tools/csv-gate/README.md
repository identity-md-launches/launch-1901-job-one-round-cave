# CSV Change Gate

Check a proposed CSV update against explicit row limits and an allowlist of
editable columns. This Python 3.10+ standard-library tool computes a fresh
exact reconciliation, returns every difference, and says whether that update
fits the declared limits. It never changes either CSV or applies a patch.
Run from the repository root; keep the sibling `csv-reconcile/` folder.

One command shows a permitted addition and quantity edit:

```sh
python3 -B line-2/tools/csv-gate/gate.py line-2/tools/csv-gate/demo-before.csv line-2/tools/csv-gate/demo-after.csv --key item --max-added 1 --max-changed 1 --allow-change quantity
```

When tried, this exited **0**, with `accepted: true`, one added chalk row,
one changed lamp quantity (`1` to `2`) and one unchanged flint row. The nested
comparison remains `equal: false`: acceptance means the changes fit the limits,
not that the files are identical. Remove the three permission options and the
same command exits **1**, reporting both row-limit violations and the forbidden
quantity change. No output file is created.

- Repeat `--key` for a composite key. Values are exact strings, including
  whitespace, empty keys and large integers. Key changes appear as removal
  plus addition; callers must choose semantically stable keys.
- `--max-added`, `--max-removed` and `--max-changed` count **rows**, default to
  zero and include the boundary. One row with several edited cells counts once.
- Repeat `--allow-change COLUMN` for every editable non-key column. A changed
  row must fit both the changed-row limit and the column allowlist. Names match
  literally; an unused or misspelled allowance has no effect. No columns are
  ignored, and values never undergo numeric or whitespace normalization.
- Added/removed rows are governed by their row limits, not the edit allowlist.
  Allowing additions permits any values in those new rows; this is not a
  business-rule or cell-value validator. Keep the default zero for protected
  datasets, or inspect the full rows in the report.
- Every schema addition/removal and every duplicate-key group rejects the
  update, regardless of row limits. Header and row ordering alone do not.
  Duplicate occurrences remain fully visible; no automatic pairing occurs.

Exit **0** means accepted, **1** means computed but rejected, **2** means
invalid input/options or an I/O error. Invalid input emits no partial report;
errors go to stderr. JSON uses ASCII escaping, including control characters.
The report includes the effective policy, all violations, and the entire
`csv-reconcile/v1` result with source logical record numbers and exact values.
It includes no input paths, timestamps or credentials. There is no report-file
input that could substitute a fabricated comparison for fresh computation.

The reused parser admits workspace-local UTF-8 CSVs, at most 16 MiB and
100,000 data records each, with unique nonempty headers and consistent row
width. It resolves paths against the current working directory. Inputs and
reports are held in memory; output may be large. Use stable files: the two
reads are not a simultaneous filesystem snapshot. An accepted report is not
a signature, authenticated approval, evidence of correct identities or a
permission to send anything. This tool performs no network, wallet, payment,
transaction or environment-variable operation. No coin is needed.

## Checks performed

```sh
python3 -B -m unittest discover -s line-2/tools/csv-gate -v
```

All **16 tests passed**: exact/reordered data, default refusals, row limits,
allowed versus forbidden fields, multiple cells per row, schema drift,
identical duplicate keys, composite keys, multiline values, invalid policies,
CLI statuses, malformed inputs, workspace containment, inert misspellings and
escaped controls. The existing reconciler's **17 tests** also passed in an
isolated scratch copy. The retained six-row ZTO/IMD observation CSV passed a
self-comparison using `(chain_id, token_address, field)` as key. That is an
offline check of historical data, not a new balance, supply or chain claim.
