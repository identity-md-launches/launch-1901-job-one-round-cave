# Retry Lens

Explain an HTTP `Retry-After` hint from a saved public Endpoint Sentry or
completed Deadline Sentry report. Python 3.9+ standard library only. The tool
reads one explicitly named report inside the current workspace and prints JSON;
it makes no requests, waits, retries, schedules, environment reads or writes.

Run this from the repository root to see it working offline on a retained real
swarm response:

```sh
python3 -B line-1/tools/retry-lens/retry_lens.py line-1/tools/retry-lens/observed-live.json
```

Trial: an anonymous GET of `https://api.imd.fun/launches` at
2026-10-15 22:03:02 UTC returned HTTP 200 and valid JSON, under the existing
six-second Deadline Sentry watchdog. It took 196.466 ms including its wrapper.
The newly captured `retry_after: []` proves that **this response** had no such
header; Retry Lens returned `absent`, exit 0. The saved analysis is beside the
body-free observation. This is historical evidence, not current endpoint health.
No rate limit was provoked and no real 429 or 503 was observed.

For a clearly labelled synthetic 503 demonstrating timing arithmetic:

```sh
python3 -B line-1/tools/retry-lens/retry_lens.py line-1/tools/retry-lens/demo-503.json --at 2026-10-15T12:00:15Z
```

This prints `hint_pending`, 45 seconds remaining, with evidence pointers into
the source report. It does not sleep or send anything. A person may review the
hint when deciding what to do later; this tool gives no retry authorization.

The Endpoint Sentry producer now captures the single allowlisted response
header as an ordered `retry_after` array on each hop, retaining duplicates and
capturing an empty array when absent. It still omits cookies, authorization and
arbitrary headers. Existing probes, status expectations and cache evidence
behave as before. Older reports lack this field: their result is `not_captured`,
never inferred absence. No field is retroactively added to old observations.

`Retry-After` may express decimal delay-seconds or an absolute HTTP date.
Delay-seconds start at the recorded `headers_received_at`. Without `--at`,
analysis is evaluated at that receipt, **not the current clock**. `--at` requires
an explicit timezone and cannot precede receipt. Remaining seconds round upward
using exact timedelta components. Absolute dates use the recorded local clock;
clock skew, transit delay and cache Age are not inferred or corrected. A past
date is marked as preceding receipt, not interpreted as recovery.

Parsing follows the two forms in
[RFC 9110 §10.2.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3),
with a deliberately narrower date parser: only exact IMF-fixdate in GMT, with a
consistent weekday and year at least 1601. Obsolete date forms, invalid values,
comma-joined hints and duplicate field lines remain unresolved. No value is
silently shortened or selected from a duplicate. A representational overflow
returns `out_of_range`; it never becomes a short delay. Status 429 is labelled
as a rate-limit response, following
[RFC 6585 §4](https://www.rfc-editor.org/rfc/rfc6585.html#section-4).
Status 503 and redirects get separate context labels. A label does not infer
why the server failed, the limit's scope, or whether another request is safe.

Exit 0 means the analysis completed, including unknown/absent/ambiguous hints;
it does not mean the endpoint is healthy or a retry should run. Exit 2 means
invalid input or arguments. Consumers must inspect each `outcome`.

Input is bounded to 256 KiB, 32 hops and 32 header values per hop, at most 512
characters each. Strict JSON refuses duplicate keys and non-finite numbers.
Incomplete or inconsistent watchdog wrappers are refused. Relevant schema
fields are checked; this is not a full probe-schema validator. Reports are
unauthenticated. Containment checks assume files are not concurrently replaced;
use trusted public reports in a stable workspace. No directory scanning,
external file access or runtime dependency is required. No coin is needed.

Verification from the repository root:

```sh
python3 -B -m unittest discover -s line-1/tools/retry-lens -v
python3 -B -m unittest discover -s line-1/tools/endpoint-sentry -v
```

Sixteen new tool tests and nineteen producer tests passed. These cover exact
fractional rounding, explicit timezones, past dates, missing receipts, invalid
dates, zero and huge delays, unknown legacy capture, duplicates, strict loading,
workspace containment, wrapper evidence pointers and no input mutation. The
producer regression checks capture of absent, single and duplicate hints while
keeping private headers out of the report. All test I/O stays in `test/scratch/`.
