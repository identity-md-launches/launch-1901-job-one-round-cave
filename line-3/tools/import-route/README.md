# Import Route

Explain why one local Python module can reach another through explicit imports,
without importing or executing the inspected project. Useful when reviewing an
unfamiliar worker, checking a dependency boundary, or tracing a coupling before
an edit. Uses only Python's standard library (Python 3.10+), offline.

From the repository root, run:

```sh
python3 -B line-3/tools/import-route/route.py line-3/tools/import-map/examples main pkg.helper
```

Tried locally: `main -> pkg.engine -> pkg.helper`, distance two, with
`main.py:1` and `pkg/engine.py:1` as source evidence. The example's unresolved
import and cyclic component remain visible. `observed-example.json` retains
the complete result, including hashes of every admitted source file.

On actual worker source, this command exited zero with a one-edge route and
no scan warnings; `observed-source.json` retains that source-only observation:

```sh
python3 -B line-3/tools/import-route/route.py line-1/tools/deadline-sentry test_deadline_sentry deadline_sentry --json --strict
```

Supply the import root (`src/` for a src-layout project) and exact dotted module
names. Routes follow imports forward. Among equally short paths, sorted BFS
chooses the lexicographically first module sequence. Each hop includes all
matching AST import sites. Equal endpoints produce a zero-edge route; this
does not establish a cycle. Unknown names are refused rather than called
unreachable. Import Budget collects source once; Import Map analyzes those
same bytes. The JSON inventory hashes bind evidence to the admitted snapshot.
Ship this folder alongside `../import-budget/` and `../import-map/`.

`--json` emits structured evidence. Exit codes: 0 for a route, 1 for no route
or a strict warning, 2 for unknown endpoints, input/scan errors or exceeded
budgets. `--strict` also returns 1 for parse/import issues, dynamic calls or
cycles anywhere in the map. Refusals emit no partial route. The inherited
limits are 1,000 Python files, 262,144 bytes per file, 8,388,608 source bytes,
20,000 directory entries and depth 64; override with `--max-files`,
`--max-file-bytes`, `--max-total-bytes`, `--max-entries`, `--max-depth`.

Reproduce the eight new behavioral checks:

```sh
python3 -B -m unittest discover -s line-3/tools/import-route -v
```

All eight passed, including 70 random graphs checked for all endpoint pairs
against Floyd–Warshall, directed/disconnected graphs, tie breaking, a
1,800-module path, relative imports and aliases, duplicate evidence sites,
retained warnings, execution traps, snapshot hashes, and CLI refusals. The
12 mapper and 15 collector regressions also passed: 35 checks total.

This traces the existing explicit static graph, not Python runtime behavior.
Dynamic imports, package initialization, external packages and runtime path
changes remain incomplete. Conditional imports may never execute; parse
errors and collisions can hide edges. An unreachable result is not proof of
isolation. Input budgets do not cap CPU, output, process memory or elapsed
time. Use a stable tree inside the workspace; this is not a filesystem sandbox.
No coin or chain data is needed for source dependency analysis.
