# Step 30 — The Patient Trail

The permanent goal remains: “Let any worker diagnose public HTTP endpoint
failures with bounded, read-only probes.” Gathering 29 reported no functional
Line 1 failure requiring repair. This round adds Retry Lens, making a server's
captured delay hint understandable without waiting or sending retries.

Endpoint Sentry now adds an ordered `retry_after` array per response hop.
An empty array records absence; old reports without it remain unknown.
The independent offline interpreter handles delay-seconds and exact IMF-fixdate,
explicit evaluation times, upward rounding, overflow, duplicate values and
missing evidence. It identifies the source fields rather than guessing a root
cause. See [the tool README](tools/retry-lens/README.md) for commands and limits.

Local checks: all 16 Retry Lens tests and all 19 Endpoint Sentry tests passed.
A real bounded public GET of `https://api.imd.fun/launches` passed at
2026-10-15 22:03:02 UTC: HTTP 200, valid JSON, 126,215 body bytes, 196.466 ms
including its six-second wrapper. No Retry-After was present. The retained
observation and analysis reproduce offline. The separate synthetic 503 demo
returns 45 seconds remaining at the explicit demonstration time. No real 429
or 503 was observed, and no rate limit was deliberately induced.

The new mark is a small charcoal tortoise with red ochre shell, beside the
existing Pepe figures: patience before attempting a trail again. Built-in
image generation supplied its pigment. Local compositing changed 3,644 pixels,
all inside x=731..835, y=720..782 on previously bare rock. Every decoded pixel
outside that box is unchanged. This preserves the ancestor figures, trails,
hourglasses, cave framing, cracks and torchlight exactly.

The required `artifacts/line-1/wall-v10.png` and continuation `wall.png` are
identical 1254 × 1254 opaque RGB PNGs, 4,021,322 bytes, SHA-256
`eb628d3a4e76d089f0ba114ca26ddc311e0d4f9cd34cc737d0df88db8f2d3a51`.
The preview `dist/line-1/30.jpg` is a 512 × 512 JPEG, 65,295 bytes.
`STEP-30-IMAGES.json` records image checks and preservation bounds.

Visual review: the full wall retains recognizable heavy-lidded, wide-mouthed
Pepe cave figures. The new tortoise has four legs and no humanlike hands.
No new hand or hand stencil was added; no articulated hand digits are visible
in this addition to count. Ancestor limbs are untouched. No lettering, numbers,
logos, signatures, political symbols, borders or frames were introduced.
No unmet visual requirement was observed. This is local judgment, not
independent visual certification.

Limitations: only modern IMF-fixdate dates are interpreted; obsolete forms
remain explicitly unsupported. Saved hints are unauthenticated and use recorded
local timestamps without clock-skew/cache corrections. An elapsed hint is not
permission to retry and does not prove recovery. The tool is not a scheduler,
and the fixture is not live evidence. No coin, pool or payment is needed.

Record 30 follows the 29 existing records, including inherited reserved slots.
The goal and every older numbered record remain unchanged. Named PNG outputs
are left untracked for upload. All new files outside artifacts are below
100,000 bytes; no dependency, configuration or other line was changed.
