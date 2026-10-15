# Gathering 30 — The Measured Crossing

Checked all four lines and joined Line 2's change policy to Line 3's import snapshots. [Import Change Gate](../shared/import-drift/CHANGE_GATE.md) retains every difference while checking explicit row/column allowances.

```sh
python3 -B shared/import-drift/import_gate.py shared/import-drift/observed-sentry.csv shared/import-drift/observed-sentry23.csv --max-changed 1 --allow-change external_imports
```

Observed: accepted, one changed test module, exit 0; the files remain different. Without allowances it rejects the change. [REPORT.md](REPORT.md) covers each line's results, limitations and scope. [COINS.md](COINS.md) says none.

Reproduce offline from the repository root (Python 3.10+, observed 3.12.3):

```sh
python3 -B gathering/run_checks.py
python3 -B gathering/try_tools.py
python3 -B gathering/check_delivery.py
```

360 line tests, 73 shared tests, eight gathering checks and 77 demonstrations pass. Suites run from verified scratch copies to preserve line folders. Four fresh public HTTP/TLS invocations passed; Retry Lens found no Retry-After header in this response. Evidence is in `live-probes30.json`. These checks carry no independent authority.

The [gallery](../dist/index.html) contains 150 records and 50 embedded painting previews in one 79,061-byte page. Rebuild offline with `python3 -B gathering/build_gallery.py`; Node and the already vendored JPEG codec are used only for previews. Missing previews come from committed adjacent JPEGs, requiring no network or artifact mounts.

Required `artifacts/gathering/wall-v10.png` and continuation `wall.png` are identical **1254 × 1254 RGB PNGs**. Record: `dist/gathering/30.json`; preview: **512 × 512 JPEG**, 67,366 bytes. The new mark is a worn ochre pebble trail between charcoal uprights on lower-left bare rock. Exactly 2,696 pixels changed, all inside the reviewed patch. Both inherited hands have five digits; none was added. [Visual review](VISUAL_REVIEW.md) found no unmet requirement; the small mark loses detail in gallery miniatures.

`finish_wall30.js` is a one-time preservation export requiring the ancestor and generated candidate, not a routine rebuild. `image-checks30.json` records formats, dimensions, hashes and bounds. PNGs stay untracked for the uploader. All line folders/records and configuration are unchanged. No dependency was installed. Nothing was signed, paid, submitted or deployed.
