# Plan: Review-store disposition reconciliation

- **Date:** 2026-10-02
- **Workflow:** plans
- **Origin class:** self-serving
- **Class:** fix-class
- **Priority:** medium

Backlog origin: docs/history/backlog/2026-10-02-review-store-disposition-reconciliation.md

## Review Scope

Paths this plan touches:

- `scripts/review_store_disposition_inventory.py` *(new)*
- `scripts/test_review_store_disposition_inventory.py` *(new)*
- `docs/history/review-store-disposition-ledger.md` *(new)*
- `scripts/machinery_registry.json`
- `docs/history/backlog/` (new rows filed by Task 2, only where the reconciliation yields terminal form backlog-row)

The store (`docs/reviews/`, a gitignored record store of md + stats.json pairs) is a read-only witness: no review record's bytes are modified. Two store facts bound this plan: the store's records span at least three schema eras (a pre-2026-09-30 era whose records largely carry a counts dict WITHOUT a `blocking_open` field — a minority lack a counts key entirely — and a current era with `counts.blocking_open`; the normalization ladder keys on the absence of each aggregate, never on the counts key itself), and `scripts/review_retention.py` prunes complete record pairs by filename date on a rolling cutoff, so the ledger — not the store — is the durable home of every disposition this plan writes.

## Terminology and core concepts

- **Canonical record**: a `.stats.json` in the store that `scripts/review_record_selection.py`'s selection contract enumerates — the `.backup-<timestamp>` copies are counted informationally only and are NEVER enumerated, `.md.stats.json` doubles are not canonical, and sidecar orphan halves are not review records. The inventory reuses that selection contract (importing the module where importable, otherwise spelling the same exclusions), rather than a bare glob.
- **Blocking signal (normalized)**: a record's open-blocking count read through the store's actual schema eras, in priority order: `counts.blocking_open` (current era); top-level `blocking_open_count` (legacy era); `blocking_totals.blocking` (legacy era); otherwise the count of findings whose own `blocking` flag is true when `findings` is a list of dicts (oldest era). Records where none of these resolve are `schema: unknown-blocking` — they are inventoried in the findings table but NEVER silently treated as zero.
- **Un-dispositioned finding**: a finding in a canonical record, at that series' LATEST round, whose normalized triage is not a terminal state. Normalized triage maps the store's real vocabulary (which includes values beyond the canonical four — `open`, `fix`, `drop`, `backlogged`, and prose sentences) onto {un-dispositioned, terminal, unmapped}: canonical terminal values (`fixed`, `folded`, and equivalents listed in the script's mapping table) are excluded; everything unmapped is INCLUDED as un-dispositioned and additionally surfaced in an unmapped-triage section, so the mapping's blind spots are visible instead of silent. Findings with no triage key are included (`triage: absent`). Findings in superseded rounds are covered wholesale by their series' terminal round (terminal form `superseded-in-series`, one ledger line per series, not per finding).
- **Unresolved blocking series**: a series whose latest canonical round has a normalized blocking signal > 0.
- **Terminal disposition forms**: exactly one per finding or series — `fixed-here` (naming the commit), `accepted-risk` (one line with the reason), `superseded-by` (naming the record or plan that resolved it), `superseded-in-series` (wholesale, for superseded rounds), or `backlog-row` (naming the filed item under `docs/history/backlog/`).
- **The ledger**: one tracked document, `docs/history/review-store-disposition-ledger.md`, with two sections — `store-derived` (rows from the Task 1 inventory) and `receipt-derived` (findings cited only in state-file receipts, which no store scan can see; disjoint from store-derived by construction). It lives tracked because the store itself is gitignored and retention prunes it; each ledger line names the store filename it dispositions so the line survives the record's pruning.

### Task 1: the inventory script and its selftest

Files:
- `scripts/review_store_disposition_inventory.py` *(new)*
- `scripts/test_review_store_disposition_inventory.py` *(new)*

CLI: `inventory --repo ROOT [--reviews-dir docs/reviews] --out FILE`. The script enumerates canonical records only (selection contract above), normalizes each record's shape per the era rules above, and writes a markdown ledger skeleton to FILE: the un-dispositioned findings table (slug, round, finding id, severity, pattern, normalized triage, consequence trimmed to 140 chars), the unresolved blocking series table, an unmapped-triage section, a `schema: unknown-blocking` count, and a skipped-shape count (records whose JSON is valid but whose shape defeats even the normalization arms — skipped and counted, never silently dropped). Stdout carries one summary line (`inventory: N findings, M series, K records scanned, S skipped-shape, U unknown-blocking`). Read-only over the store. Exit codes: 0 when the inventory is written (any result, including empty — a valid-JSON record whose shape defeats the normalization arms is skipped and counted in skipped-shape, never an abort); 2 tool failure (store directory missing or unreadable, or malformed JSON). There is no exit-1 semantic: the guard family reserves 1 for a gate's semantic negative, and an inventory writer has none — stating this explicitly so the family contract is not misquoted.

- [ ] Write the selftest first: unittest scratch-dir fixtures covering, at minimum: (a) a counts-era record with a recorded finding; (b) a legacy record with top-level `blocking_open_count` > 0 and no successor round; (c) a legacy record with `blocking_totals.blocking` > 0; (d) an oldest-era record with per-finding `blocking` true flags and no aggregate key; (e) a record whose `findings` is an int, one where it is None, one where it is a dict; (f) a record with round as the string "r2" and one with the round key absent (the table's round column comes from the filename-derived round either way — the body field is never load-bearing); (g) a `.backup-<timestamp>` twin and a `.md.stats.json` double that must be excluded; (h) a record with no `-r<N>` suffix; (i) an unmapped triage prose value; (j) a finding with no triage key; (k) a fully dispositioned record that must be excluded; (l) a malformed-JSON record (the exit-2 trigger) — asserting both tables, the unmapped and unknown-blocking and skipped-shape counts, the exclusion of non-canonical files, and exit codes 0 and 2 [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `python3 scripts/test_review_store_disposition_inventory.py` fails before the script exists [class: REPOSITORY_TEST]
- [ ] Implement the script; run → expect GREEN: the selftest passes [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect exit 0: `python3 scripts/review_store_disposition_inventory.py --repo . --out /tmp/ledger-skeleton.md` over the real store, with the summary line reporting a nonzero skipped-shape or unknown-blocking count only where the store's real shape drift warrants it [class: REPOSITORY_TEST]

### Task 2: the disposition ledger

Files:
- `docs/history/review-store-disposition-ledger.md` *(new)*

Run the Task 1 inventory over the real store, then for every store-derived row re-derive the terminal disposition from the receipts, the completed plans, and the review records themselves — never from this plan's text — and write one ledger line per finding (or per series, for `superseded-in-series`) in exactly one terminal form. The receipt-derived section carries the findings the origin item cites that exist only in state-file receipts, dispositioned the same way. The origin item's named instances are re-derived anchors, not mandates, and the ledger must record where the origin's own claims fail verification: in particular the origin's claim that the migrate-crypto-tax-lessons r2 series is unresolved is FALSE (the store holds an r3 with `blocking_totals.blocking` 0 and prose stating all three r2 blocking findings resolved — terminal form `superseded-by` naming that r3), while the genuinely unresolved series the origin missed — the post-landing primary-checkout reconciliation r5 with blocking_open 2 — must appear. Findings whose terminal form is `backlog-row` get new files under `docs/history/backlog/` in the standard item shape, each with a Dedup probe naming this plan's origin item (a prose discipline; no script enforces it). The ledger's header states the standing bookkeeping duty: every future un-dispositioned finding receives a terminal line or a backlog row at the owning plan's completion pass, and ledger lines survive `scripts/review_retention.py` pruning by carrying the store filename each line dispositions.

- [ ] Author the ledger from the inventory output plus the receipt-derived section, one terminal line per finding and per series, including the crypto-tax correction and the missed r5 series [class: IMPLEMENTATION_REQUIRED]
- [ ] File backlog rows for the findings whose terminal form is backlog-row [class: IMPLEMENTATION_REQUIRED]

### Task 3: machinery registration

Files:
- `scripts/machinery_registry.json`

Add one entry per the registry's schema (re-derive the field shapes from the existing entries; do not copy this plan's guess): disposition keep, kind script, paths `["scripts/review_store_disposition_inventory.py"]`, with the witness referencing the ledger document (`docs/history/review-store-disposition-ledger.md`), which documents the script's role and is tracked. Capture the check baseline BEFORE editing the registry: the store's pre-existing check failures (the registration drift the machinery-inventory-upkeep plan owns, which may or may not have been executed by a peer lane when this task runs) are out of scope; this task's check claim is no NEW failures against the live baseline, not a zero count.

- [ ] Capture the `--check` baseline, add the registry entry, and run → expect unchanged: `python3 scripts/machinery_inventory.py --check` reports exactly the captured baseline, none naming the new script [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect OK: `python3 scripts/test_machinery_inventory.py` [class: REPOSITORY_TEST]

### Task 4: validation

Files: none (verification only)

- [ ] Run → expect OK: the Task 1 selftest [class: REPOSITORY_TEST]
- [ ] Run → expect exit 0: the hygiene scan [class: REPOSITORY_TEST]
- [ ] Run → expect exit 0 per round record: `python3 scripts/validate_review_staging.py --hard <round-md-path> --source-plan <round-bytes-file>` for each authored round record [class: REPOSITORY_TEST]
- [ ] Run → expect exit 0: `python3 scripts/plan_readiness.py` on the final bytes [class: REPOSITORY_TEST]

## Assumptions

- Bookkeeping only: no new gates, no skill-prose changes; the enforcement story is the inventory script plus the ledger's standing duty sentence.
- An accepted-risk line is a valid terminal disposition under the machinery cost-benefit adjudication; this pass writes dispositions and never re-litigates a deferral.
- The store's md records are never annotated in place, and the reason is survivability, not digests: the store is gitignored (dispositions must live somewhere tracked) and `scripts/review_retention.py` deletes store records on a rolling date cutoff (the ledger is the durable record that survives). The only byte-level gate over historical record bodies is `summarize_review_stats.py`'s private local baseline, which is not a repo gate and does not motivate this design.
- The origin item's store-shape claims predate this plan's corpus verification; where they conflict with the bytes, the ledger records the correction and this plan's Review Scope treats the origin as an anchor to re-derive, not a spec.

Decision points requiring a grill: whether the ledger or the findings' own records carry dispositions (resolved: the single tracked ledger — the store is gitignored and retention-pruned, so record-side annotations would not survive, and the only historical-bytes gate is an untracked local baseline, not a reason to keep dispositions out of the store); whether the inventory script refuses or warns on a missing store (resolved: missing or unreadable store is exit 2 tool failure, matching the family precedents where unreadable input is a tool failure, and the script carries no exit-1 semantic because an inventory has no gate-negative outcome to express).
