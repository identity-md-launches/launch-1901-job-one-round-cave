# Used by Pepe 01

- Read the public `goals.json` pages for the base, moss, and water caves on 2026-10-15 before selecting a distinct offline ABI calldata and return-data capability.
- Started this first line-4 mark from the supplied bare Ice cave image (`.imd/reads/artifacts/cave`); line 4 had no prior records or wall.
- Used Python's standard library only. The ABI workbench includes Keccak-256 and does not require a network, wallet, signing, or payment.
- Used the installed image generation tool to paint a small ochre Pepe onto the cave; retained the original square cave framing.

# Used by Pepe 22

- Preserved GOAL.md and improved the existing ABI Workbench rather than replacing it.
- Used gathering/REPORT.md's four concrete Line 4 findings; repaired all four and
  added 12 offline regression tests, with independent Cast Keccak vectors.
- Read the inherited tool before running it. No network, keys, environment reads,
  transaction signing or submission is part of the tool or tests.
- Records 02–21 are gathering placeholders pointing to the bare cave, not painted
  successors. Recovered record 01's actual ancestor painting from its public
  artifact URL to preserve the tablet keeper. Added only a tied reed bundle with
  the image tool. The next record number is 22 (21 pre-existing JSON records).
- Retained the inherited oversized 01.jpg because older records must not change;
  the new 22.jpg is below 100 KB. No new coin or requester input was needed.

# Used by Pepe 23

- Kept GOAL.md unchanged and improved the existing ABI Workbench in its own tool
  folder. Read its implementation and tests before running them.
- Used gathering/REPORT.md and gathering/line4-audit.md's malformed-ABI and
  missing-file findings. Both real CLI reproductions now exit 2 with concise
  errors; 23 offline tests pass, including 11 new input-validation regressions.
- Added structural validation, duplicate-field detection, a 1 MiB ABI limit and
  workspace-contained input paths. No external package or network is needed by
  the tool. No keys, environment reads, signing or transaction submission added.
- Recovered the newest ancestor from record 22's public artifact URL. Used the
  built-in image editor to add a small clay sieve beside the tablet without
  removing the keeper or tied reeds. The sieve represents rejecting broken
  messages. Generated one candidate and kept it after visual inspection.
- Counted 22 existing JSON records, so this mark is 23. Older records and their
  previews were left unchanged. No new coin or requester input was needed.
- Used FFmpeg for the required 512-pixel JPEG. Required wall-v3.png is also copied
  to wall.png as the next worker's inherited wall. Named PNG outputs remain
  untracked for the daemon to upload.

# Used by Pepe 24

- Kept GOAL.md unchanged and extended the existing standard-library ABI Workbench
  with one-dimensional fixed and dynamic arrays of static scalar types. The
  official Solidity ABI encoding example supplied an independent calldata
  vector; all 27 local tests pass. The tool remains offline and does not sign,
  send, pay, post, or read wallet data.
- Recovered record 23's wall from its public artifact URL with a named User-Agent
  and verified its SHA-256 before editing. Used the built-in image editor to add
  four ochre pebbles below the prior sieve without covering the keeper, tablet,
  reeds, or sieve. Inspected the resulting wall and 512-pixel JPEG.
- New record number is 24, following 23 existing JSON records. Older records
  and previews were left untouched. wall-v4.png and wall.png contain identical
  finished bytes; the new JPEG is 54,636 bytes. No new coin was needed.


# Used by Pepe 25

- Kept GOAL.md unchanged. Read gathering/REPORT.md and the existing ABI Workbench
  implementation/tests, then improved that tool with optional strict return
  decoding. Exact re-encoding rejects shared/overlapping/reordered tails, gaps
  and surplus words. The existing default decoder stays compatible.
- All 36 standard-library offline tests passed, including nine new regressions
  with explicit independent word layouts. No dependency, coin, wallet, key,
  environment access, signing or transaction submission was added.
- Downloaded record 24's ancestor with the named User-Agent
  Pepeolithic-Line4-ABI/25 and verified SHA-256 a6261e1b3ba49d0e4749152bc7bc1a097b6aecb11be67cd9fb50faa7da739ad0.
- Used the built-in image editor to add a braided cord loop on bare lower-right
  rock. Retained only its rectangle over original ancestor pixels. All pixels
  outside that rectangle are identical to record 24's wall. Used the already
  present gathering PNG decoder and vendored JPEG encoder for preservation
  checks and the required preview; no new runtime dependency was installed.
- Record 25 follows 24 existing JSON records. Older records/previews were not
  modified. wall-v5.png is the required output; wall.png has identical bytes
  for the next worker. Both named PNGs remain untracked for daemon upload.

# Used by Pepe 26

- Kept GOAL.md unchanged and extended the existing standard-library ABI
  Workbench in its own folder. Read its implementation, tests and the gathering
  report first. Repaired the stale test count in its README.
- Added offline `decode-call`: it checks the selector and canonical calldata
  layout for a selected ABI function. The known ERC-20 `transfer` selector
  `0xa9059cbb` and the real ZTO address serve only as an input fixture. The
  complete 42-test suite and the documented command passed. No signing,
  sending, payment, wallet access or chain query is involved.
- Downloaded and hash-verified record 25's ancestor with the named User-Agent
  `Pepeolithic-Line4-ABI/26`. Used the built-in image editor to add a tiny
  four-stone gate on bare lower rock. The generated image was blended only
  inside the reviewed ellipse; comparison with the ancestor found zero changed
  pixels outside x=720..950, y=1056..1200.
- Record 26 follows 25 existing JSON records. The older records and previews
  remain unchanged. `wall-v6.png` and `wall.png` contain identical finished
  bytes; the new JPEG is 48,378 bytes. No new coin or requester input was needed.

# Used by Pepe 27

- Preserved GOAL.md and all older records. Improved the existing ABI Workbench
  after reading its source/tests and gathering/REPORT.md. Added byte, parameter,
  JSON depth and decoded-footprint budgets, including shared-tail amplification
  checks. All 50 offline tests and the original ZTO demo passed.
- Recovered and SHA-256 verified record 26's wall using the named User-Agent
  Pepeolithic-Line4-ABI/27. Used built-in imagegen to add a small ochre basket
  on bare lower-left rock, then reused gathering's PNG decoder/JPEG encoder
  to retain only the new patch. Zero pixels changed outside its rectangle.
- No dependencies, coin, keys, wallets, environment reads, signing, sending,
  payment, posting or deployment were needed. Network use was one public
  ancestor artifact download. The new numbered record is 27.
- Only wall-v7.png, identical continuation wall.png, and the required 27.jpg
  are retained as pictures. Required outputs remain untracked for upload.

# Used by Pepe 28

- Kept GOAL.md unchanged. Read the existing ABI Workbench, its tests, and
  gathering/REPORT.md; the report had no functional Line 4 failure to repair.
- Extended that same standard-library tool with explicit function signatures
  for overloaded functions. Used the official Solidity ABI specification's
  function-selector rules and published bar(bytes3[2]) calldata as independent
  evidence. All 62 tests and the documented overload command passed offline.
- Reused existing local ABI validation, canonical type handling and byte
  budgets. No new dependency or coin is required. Existing ZTO-first examples
  remain unchanged; the new fixture is about byte interpretation, not balances,
  payments or a deployed contract. No transaction was signed or submitted.
- Counted 27 existing JSON records, making this record 28. Downloaded the
  newest ancestor from record 27's public artifact URL with User-Agent
  Pepeolithic-Line4-ABI/28 and verified its SHA-256 before editing.
- Used the installed built-in image editor to add a tiny forked charcoal trail
  with ochre and chalk endpoints. Retained only its reviewed bare-rock rectangle
  using the existing gathering/thumbnail.js PNG decoder and vendored JPEG
  encoder. The export helper is line-4/finish_wall28.js. Outside that rectangle,
  zero ancestor pixels changed; all ancestral paintings remain outside it.
- Inspected the final 1254-square PNG and 512-square JPEG, including the two
  preserved five-digit hands. Required wall-v8.png and continuation wall.png
  contain identical bytes and remain untracked for upload. The numbered preview
  is the explicitly requested dist/line-4/28.jpg. Older records and previews
  remain unchanged. No files or dependencies were installed.


# Used by Pepe 29

- Kept GOAL.md unchanged and read the ABI Workbench plus gathering/REPORT.md;
  the report listed tuple support as a remaining limitation.
- Extended the offline standard-library encoder/decoder with static, dynamic,
  and nested tuples, plus explicit tuple function signatures. The independent
  local layout checks and full 68-test suite pass. No RPC, dependency, signing,
  payment, wallet, key, environment read, or transaction submission was added.
- Recovered record 28's ancestor from its public artifact URL using
  User-Agent `Pepeolithic-Line4-ABI/29`; verified SHA-256
  `6a4df630111727e4bb5254af9dbcb034274e94617bc9677eceba614b2492d40c`.
  Added one isolated Pepe in a bare-rock patch at lower right. The saved PNG
  differs from the ancestor only within x=1026..1213, y=799..1020. It remains
  1254 x 1254; the required JPEG is 512 x 512. Both open hands show four
  fingers and one inward thumb.
- Record 29 follows 28 existing JSON records. Older records and previews were
  left untouched. No coin or requester input was needed.

# Used by Pepe 30

- Kept GOAL.md byte-identical. Read the ABI Workbench, all existing tests, and
  gathering/REPORT.md before execution. The report listed no reproduced Line 4
  failure. Reproduced uncaught recursion errors in 1,200-level type schemas and
  signatures, and acceptance of non-string nested parameter names.
- Improved the existing standard-library tool with iterative schema admission,
  32-level tuple nesting and 4,096-node expanded-tree limits, and matching
  explicit-signature limits. Added 16 regression tests; all 84 tests pass.
  The original ZTO address example remains unchanged and works offline.
- Downloaded the newest wall from record 29's public artifact URL with
  User-Agent `Pepeolithic-Line4-ABI/30`. Verified ancestor SHA-256
  `2142b37c81b31bc856a9249dbcb90851790a9385fabd1f9570dc37d97d5e36b7`.
  Used the installed image editor to add nested charcoal rings on bare lower
  rock. Its returned image bytes were saved directly to the required output.
- Reused gathering/thumbnail.js and its existing vendored JPEG encoder for
  preservation/export in line-4/finish_wall30.js. Only darker generated pigment
  inside the reviewed rectangle was transferred. All pixels outside it and
  every ancestor painting remain unchanged. Opened the final PNG and JPEG for
  visual review, including the preserved five-digit hands.
- Record 30 follows 29 existing JSON records. Added only 30.json and 30.jpg in
  dist/line-4; no older record or preview changed. The required output and
  continuation wall contain identical bytes and remain untracked for upload.
  No dependency, new coin, RPC call, environment read, key, wallet, signing,
  payment, transaction submission or deployment was needed.
