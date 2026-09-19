# Plan: Review records contract (4 origins)

Backlog origins (scope of record, all HIGH):
- `docs/history/backlog/2026-09-16-review-record-kinds-and-sidecar-contract.md`
- `docs/history/backlog/2026-09-16-review-round-record-selection.md`
- `docs/history/backlog/2026-09-16-review-artifact-overwrite-guard.md`
- `docs/history/backlog/2026-09-16-review-backlog-redaction-gate.md`

Refiled on 2026-09-18: `docs/history/backlog/2026-09-15-review-sot-consolidation-gate.md` stays a standalone churn-reduction backlog item; this plan no longer carries it.

Revision 2026-09-18 (approved scope split): the kind classification report (former Task 2; no named consumer) and the consumer-row disposition matrix (former Task 7; scales with what ships) are deferred and recorded under Non-goals; the one-sentence producer declarations from the former Task 7 moved into Task 2 because the date fence makes a kind declaration mandatory for every producer post-fence; the redaction gate is redesigned as a capture-time check that reuses the existing public-hygiene scanner (one explicit-paths mode on the existing script; no new gate script, no done-workflow arm). The 2026-09-17 r5 certification does not cover these bytes; re-certify before execution (standing maintenance pre-step).

## Terms

- **Record kind**: the new `record_kind` value on every version-1 sidecar and the matching Markdown Metadata line `Record kind:`; one of `canonical`, `reconciliation`, `worker-evidence`, `legacy-import`.
- **Canonical record**: a full review-staging Markdown plus `.stats.json` sidecar pair satisfying every current gate; the only kind that can certify a clean verdict or satisfy a readiness gate.
- **Sidecar**: the `.stats.json` JSON twin of a staging Markdown record, written in the same pass per `review-staging`.
- **Kind fence**: the validator constant `RECORD_KIND_SIDECAR_MIN_DATE` (implementing-commit date plus one day, pinned in the same commit); version-1 records dated on or after it must declare `record_kind`; earlier records are accepted-legacy and exempt, mirroring `EXTENDED_SIDECAR_MIN_DATE` and `COVERAGE_SIDECAR_MIN_DATE`.
- **Selection helper**: the new `scripts/review_record_selection.py`; enumerates matching records and sidecars (ignoring backup pairs), selects reuse or the next `-r<N>` round, refuses destructive replacement, and emits the selected paths before workers launch.
- **Overwrite guard**: the selection helper's refusal rule: a target record that exists whose sidecar `source_digest` differs from the caller-supplied digest of the bytes about to be reviewed is never replaced; the refusal names exactly the two supported actions, `--explicit-new-round` (allocate the next round) or `backup` (the explicit archival operation). The digest is the only comparison input; it already has a persisted home (the sidecar `source_digest`), so the helper invents no second state store.
- **Immutable backup**: a timestamped byte-identical copy pair (Markdown plus sidecar) written under the resolved reviews directory before any permitted same-pass replacement; the copy path is recorded in the new record's Metadata, and backup pairs are excluded from record enumeration (counted informationally only).
- **Capture hygiene check**: the receiving-review Backlog capture step that runs `bash scripts/scan-public-hygiene.sh --files <draft-path>` over the composed, still-uncommitted backlog item; the shared deny-patterns file and the script's two built-in patterns stay the only rule sources; a nonzero verdict stops the capture until the draft is fixed in place, never by widening the patterns.
- **Skill-gate marker**: the per-(project, session) consent marker at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`, refreshed before every gated plan-file write per `agents/hooks/skill-gate/README.md` ("Marker WRITE RECIPE (plans class)"), including execution-time plan mutations such as checkbox marks.
- **Session key**: the raw session id emitted by the shared `session_channel.py` subprocess; the empty-after-strip `no-session` literal and the `sha1(value)[:16]` transform are applied by `skill_gate.py` and the marker recipe, not by the channel helper.

## Assumptions

- assume the readiness validator inherits canonical-kind gating through the existing shared sidecar gate instead of a second implementation; basis: `scripts/plan_readiness.py` module docstring (the shared sidecar gate owns schema, source_kind, and digest checks).
- assume additive top-level sidecar fields are transparent to existing script consumers; basis: consumer probes show `.get`-based field reads in `summarize_review_stats.py`, `execute_plan_runtime.py`, and `execute_plan_address_fanout.py`, and unknown-key rejection lives only at the validator boundary.
- assume `RECORD_KIND_SIDECAR_MIN_DATE` is pinned to the implementing-commit date plus one day and the validator selftests derive fixture dates from the imported constant, never a hardcoded date; basis: the `EXTENDED_SIDECAR_MIN_DATE` and `COVERAGE_SIDECAR_MIN_DATE` fence precedents in `validate_review_staging.py`.
- assume execute-plan address-fanout finding files are patch evidence, not review records; they stay recorded via `extensions.address_fanout` and gain no record kind; basis: the Address fan-out accounting contract in `review-staging`.
- assume worker-evidence records are staged review records carrying one worker's evidence (focused or partial records, per-worker evidence documents), each still requiring a sidecar twin; basis: origin 1 minimum contract and the doing-code-review Step 2 record inventory (focused, risk, and suffixed filenames).
- assume new scripts stay standard-library-only with no new dependencies; basis: every existing tool under `scripts/` is standard-library-only.
- assume no new skills are created, so README catalog entries and skill LICENSE files are unchanged; basis: all four origins change behavior inside existing skills and scripts, and this plan's only new script is the selection helper.

Decision points requiring a grill: record_kind placement: top-level date-fenced sidecar field plus a Markdown Metadata twin, mirroring the coverage fence precedent (decision: standing pre-authorization to accept recommended options; task prompt 2026-09-16; affected: Task 1); canonical clean-exit enforcement point: inside the shared validator sidecar gate so the readiness validator inherits it (decision: standing pre-authorization; 2026-09-16; affected: Tasks 1 and 2); guard refusal semantics: differing digest always refuses without an explicit new-round or backup action, the digest is the only comparison input because it is the only one with a persisted home (sidecar source_digest), and the refusal names exactly the two implemented actions (decision: standing pre-authorization plus review r1 F1; 2026-09-16; affected: Task 3); worker-evidence field carrier: sidecar top-level fields mirrored as Metadata lines, mirroring the record_kind precedent (decision: standing pre-authorization plus review r1 F2; 2026-09-16; affected: Task 1); capture hygiene wiring: receiving-review Backlog capture runs the existing public-hygiene scanner over the composed draft through a new explicit-paths mode on the same script, the shared patterns file stays the single customization surface, and no done-workflow arm is added (decision: user-approved redesign, 2026-09-18; affected: Task 4); producer declarations for the fence: rfc-design, review-confluence-doc, and review-reconciliation declare their kinds in one sentence each so the fence cannot break unwired producers (decision: consequence of the 2026-09-18 scope split; affected: Task 2); worker-evidence boundary: execute-plan address-fanout finding files excluded from record kinds because extensions.address_fanout already records them (decision: standing pre-authorization; 2026-09-16; affected: Terms).

## Gist & Examples

Five witnessed gaps share one root: review records carry no machine-readable identity, so consumers cannot tell current canonical evidence from supplemental notes or historical imports, and nothing mechanical stands between a new review round and the prior round's bytes. This plan gives every record an explicit kind, makes round selection and overwrite protection mechanical, and runs the existing public-hygiene scanner over backlog captures before they are committed. The duplicated-document fan-out gap moved back to its standalone origin (see the refile note above).

**Origin-to-task traceability** (every task traces to a witnessed failure):

| Origin witness | Gap today | Task |
|---|---|---|
| 330 recent records audited; 39 fail the hard validator; reconciliation and worker documents are evaluated as if canonical; 629 legacy sidecars and 302 digest-less sidecars are indistinguishable from current violations | No `record_kind`; the validator has exactly one gate shape | Task 1 |
| A repeat review reused the prior canonical path and rewrote it; the rule exists only as prose in two skills | No mechanical selection before workers launch; no `Supersedes` / `Superseded by` link check | Task 3 |
| A review orchestrator deleted and recreated an ignored Markdown record and sidecar; ignored files cannot be recovered from Git | No pre-write guard; no backup before permitted replacement; no audit that historical rounds survive | Task 3 |
| Audit found 18 email-like values, 123 absolute user paths, and 35 credential-assignment patterns reachable from backlog capture | Backlog rules require prose care but no deny-pattern scan at capture time | Task 4 |

Tasks 2 and 5 carry no separate witness row: they are producer-wiring and validation tasks that propagate and verify the contract the witnessed origins above define (canonical declarations, kind-aware aggregation, and the final validation sweep).

**Before (today):** a reconciliation pass writes its recurrence ledger into a file the hard validator rejects as a broken canonical record, so the corpus shows failures that are not producer mistakes. A user asks to re-review after new commits; the orchestrator reuses `...-r1.md` and the prior findings are gone. A backlog item synthesized from a deferred finding copies a reviewer's absolute home path into a durable file.

**After (this plan):** the reconciliation record declares `record_kind: reconciliation`, carries its six output-contract labels, and validates clean without canonical finding sections, while a canonical record missing those sections still fails. The repeat request runs the selection helper, which compares the caller-supplied digest against the existing record's sidecar `source_digest`, refuses the `-r1` path on a mismatch (guard error naming the existing record and the two supported actions), allocates `-r2` under `--explicit-new-round`, links `Supersedes: <-r1 path>` forward, and marks `-r1` `Superseded by:` backward without touching its findings. The backlog capture runs the public-hygiene scanner over the composed draft before any commit; a hit stops the capture with the scanner's FAIL block naming the file and line, and the draft is fixed in place.

**Non-goals:** no historical record is rewritten or backfilled; no kind classification report mode (deferred: no named consumer; the corpus stays auditable through the validator's normal run); no consumer-row disposition matrix (deferred: it scales with what actually ships); no transformation or redaction mode with placeholder conversion and counts-only reporting (the fuller redaction policy stays open in the redaction origin item); address-fanout finding files gain no kind; no new skill is created and the only new script is the selection helper; the docs-branch and done workflow structure stays fixed.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the validator selftest, the selection-helper suite, the summarizer and usage-capture selftests, the scanner selftest with its explicit-paths cases, and the execute-plan runtime suite pass; each new gate blocks its negative witness and accepts its positive witness.
- fail-closed bias: a post-fence record without a kind is an error, never a silent pass; the guard refuses before any byte is written; the capture hygiene check treats a scanner error (missing patterns file, missing rg) the same as a hit: the capture stops.
- evidence preservation: prior records stay byte-for-byte unchanged except the separately recorded supersession marker; backups are byte-identical copies.
- contract-doc consistency: every producer that writes version-1 sidecars declares its kind post-fence, and every edited consumer skill states the shipped behavior in its own workflow text (helper run, capture check, canonical declarations).
- hygiene: no em-dash in changed Markdown and in the new files this plan creates; the two edited validators and the edited scanner keep their legacy em-dash regions frozen and stay outside whole-file em-dash sweeps; public hygiene scan exits 0.

**Done when:**
- `python3 scripts/validate_review_staging.py --selftest` passes with the new record-kind and supersession-link checks present.
- `python3 scripts/test_review_record_selection.py` passes.
- `python3 scripts/summarize_review_stats.py --selftest` passes with the canonical-only aggregation check present.
- `bash scripts/scan-public-hygiene.sh --selftest` passes with the explicit-paths cases present.
- `python3 scripts/plan_readiness.py --sweep` exits 0.
- Every producer that writes version-1 sidecars (review-plan, rfc-design, review-confluence-doc, doing-code-review, review-reconciliation, execute-plan code-review workers) declares its kind in its own workflow text.
- The public hygiene scan and the scoped em-dash sweeps (edited Markdown whole; only the new files this plan creates under the all-files mode) pass.

**Ship when:**
- Deployed runtime copies (`~/.ai-playbook/scripts/`) pick up the selection helper and the scanner's explicit-paths mode through the existing symlink and copy-sync model on their next redeploy; no cross-team action.
- Producer skills adopt the kind declarations in their next naturally staged records; no corpus migration is required or performed.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py` (record-kind gates, supersession link check, producer-naming errors, selftests; existing checks frozen)
- `scripts/summarize_review_stats.py` (canonical-only aggregation filter plus selftest case; other functions frozen)
- `scripts/review_record_selection.py` *(new)*
- `scripts/scan-public-hygiene.sh` (explicit-paths mode plus its selftest cases only; the deny-rule surface stays frozen)
- `agents/skills/review-staging/SKILL.md` (Record kinds subsection, sidecar contract table row, Metadata template line, canonical-record section, Integration Points notes)
- `agents/skills/review-plan/SKILL.md` (inlined sidecar-schema block only; every other section frozen)
- `agents/skills/doing-code-review/SKILL.md` (Steps 2-4 record-selection and worker-evidence staging only; all other sections frozen)
- `agents/skills/review-loop/SKILL.md` (mechanical gate paragraph and the Task 3 staging-section helper line only)
- `agents/skills/review-reconciliation/SKILL.md` (Output contract kind declaration only)
- `agents/skills/receiving-review/SKILL.md` (Backlog capture section only)
- `agents/skills/rfc-design/SKILL.md` (staging Step 2 sidecar sentence only)
- `agents/skills/review-confluence-doc/SKILL.md` (Steps 1 and 4 sidecar sentences only)
- `agents/skills/execute-plan/subagent-prompts.md` (code-review staging instructions only)

**Tests:**
- `scripts/test_review_record_selection.py` *(new)*
- Validator, summarizer, and usage-capture selftests live inside the production files listed above; the scanner selftest lives in `scripts/scan-public-hygiene.sh`.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_resume_watcher.py` and `scripts/test_execute_plan_resume_watcher.py`; reason: peer-session deliverables committed separately; not this plan's deliverables.
- `agents/skills/plans/SKILL.md`, `docs/maintenance/document-registry.md`, `docs/plans/2026-09-15-execute-plan-review-fix-pipeline-efficiency.md`, `docs/plans/2026-09-17-backlog-long-tail-prose-predicates-small-mechanics.md`; reason: peer-session files, not this plan's deliverables.
- `agents/skills/done/SKILL.md`; reason: the redesigned capture check adds no done-workflow arm.
- `agents/skills/review-agents/documentation.md`; reason: SOT consolidation behavior moved back to its standalone origin.
- The historical record corpus under `docs/reviews/`; reason: never rewritten by this plan.
- `README.md`; reason: no skill or catalog name changes.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
python3 scripts/validate_review_staging.py --selftest || { echo "FAIL: validator selftest"; exit 1; }
python3 scripts/test_review_record_selection.py || { echo "FAIL: selection helper suite"; exit 1; }
python3 scripts/summarize_review_stats.py --selftest || { echo "FAIL: summarizer selftest"; exit 1; }
python3 scripts/review_usage_capture.py --selftest || { echo "FAIL: usage capture selftest"; exit 1; }
bash scripts/scan-public-hygiene.sh --selftest || { echo "FAIL: scanner selftest"; exit 1; }
python3 scripts/test_execute_plan_runtime.py || { echo "FAIL: execute-plan runtime suite"; exit 1; }
python3 scripts/plan_readiness.py --sweep || { echo "FAIL: readiness sweep"; exit 1; }
bash scripts/check-no-em-dash.sh file agents/skills/review-staging/SKILL.md agents/skills/review-plan/SKILL.md agents/skills/doing-code-review/SKILL.md agents/skills/review-loop/SKILL.md agents/skills/review-reconciliation/SKILL.md agents/skills/receiving-review/SKILL.md agents/skills/rfc-design/SKILL.md agents/skills/review-confluence-doc/SKILL.md agents/skills/execute-plan/subagent-prompts.md || { echo "FAIL: em-dash in changed prose"; exit 1; }
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/review_record_selection.py scripts/test_review_record_selection.py || { echo "FAIL: em-dash in new files"; exit 1; }
# Scope note (intentional, per the never-allowed-sweep rule): the prose sweep covers the nine edited skill Markdown files; the all-files sweep covers ONLY the two new files this plan creates (vacuously green until Task 3 creates them). The two edited validators (validate_review_staging.py, summarize_review_stats.py) and the edited scanner (scan-public-hygiene.sh) are excluded from whole-file em-dash sweeps because they carry legacy em-dashes in frozen regions no task touches; their new insertions follow the same no-em-dash authoring rule.
bash scripts/scan-public-hygiene.sh || { echo "FAIL: public hygiene scan"; exit 1; }
```

### Task 1: record_kind contract in the staging gold source and the validator

Files:
- `scripts/validate_review_staging.py`
- `agents/skills/review-staging/SKILL.md`

- [ ] Add the selftest `_selftest_record_kind_contract` covering, each as its own check label: a post-fence sidecar without `record_kind` fails; a `record_kind` outside the four-value enum fails; a post-fence reconciliation record without canonical finding sections passes while a canonical record missing them still fails; a post-fence worker-evidence record whose sidecar carries top-level `worker`, `lens`, `status`, `source_ref` mirrored as the Metadata lines `Worker:`, `Lens:`, `Worker status:`, `Source:` passes, and one missing `worker` field fails (the carrier is decided: sidecar fields mirrored as Metadata lines, per the record_kind precedent; the Metadata mirror for the sidecar `status` field is `Worker status:`, so it cannot collide with the staging template's existing `- Status: STAGED` line); an explicit `legacy-import` record is accepted as historical and never eligible for a clean verdict; a `verdict: yes` record whose kind is not canonical fails; the kind is never inferred from a filename (a file named `...-reconciliation` with no `record_kind` post-fence fails as missing-kind, not treated as reconciliation); each cross-kind failure (missing twin, wrong kind, stale digest, invalid Pattern ID) yields exactly one actionable error naming the owning producer mapped from `source_kind` (plan to review-plan, rfc to rfc-design, document to review-confluence-doc, code to doing-code-review)
- [ ] Run → expect RED: `python3 scripts/validate_review_staging.py --selftest` reports FAILED on the new record-kind check labels while every pre-existing label stays green
- [ ] Implement: the constant `RECORD_KIND_SIDECAR_MIN_DATE` (implementing-commit date plus one day, pinned in this commit); enum validation on the sidecar top-level field and the Markdown Metadata `Record kind:` line (filename-leading-date fence, mirroring the freshness lines, including the mixed-fence direction checks); per-kind gate matrix where canonical keeps every current gate, reconciliation requires the six output-contract labels from `review-reconciliation` (Trigger, Recurrence map, Invariant and witness ledger, Changes made or proposed, Decision requests, Handoff) and skips canonical finding-hierarchy and coverage gates, worker-evidence requires the four top-level sidecar fields `worker`, `lens`, `status`, `source_ref` mirrored as the Metadata lines `Worker:`, `Lens:`, `Worker status:`, `Source:` (the `Worker status:` name avoids colliding with the template's `- Status: STAGED` line) and skips the same canonical gates, legacy-import is accepted as historical and excluded from clean-verdict eligibility; the coverage obligation stays canonical-only; producer-naming suffix on the four cross-kind errors
- [ ] Run → expect GREEN: the full selftest passes including the new labels
- [ ] Write the SOT prose: a `### Record kinds (RECORD_KIND_SIDECAR_MIN_DATE)` subsection in `review-staging` defining the four kinds and each minimum contract (including the four worker-evidence sidecar fields and their Metadata mirror lines), the `record_kind` row in the version-1 sidecar contract table (date-fenced required field, enum, never filename-inferred, never a silent legacy downgrade), the `Record kind:` line in the Metadata template, and the coverage-subsection trigger sentence amended to canonical-only (the coverage obligation applies to canonical `source_kind: plan` records; reconciliation, worker-evidence, and legacy-import records never require `coverage`)
- [ ] Commit: `skills: record_kind review staging contract with date fence`

### Task 2: canonical-only clean exit, aggregation, and producer declarations in consumers

Files:
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/rfc-design/SKILL.md`
- `agents/skills/review-confluence-doc/SKILL.md`
- `agents/skills/review-reconciliation/SKILL.md`
- `scripts/summarize_review_stats.py`

- [ ] Add a summarizer selftest case; given a fixture directory with one canonical sidecar (two findings) and one post-fence reconciliation sidecar (one finding), expects aggregation to count only the canonical findings for panel tuning and to report the non-canonical record separately in the output
- [ ] Run → expect RED: `python3 scripts/summarize_review_stats.py --selftest` fails on the new case (today a supplemental sidecar's findings fold into the aggregate)
- [ ] Implement the canonical-only filter in `aggregate_sidecar` and the separate non-canonical count line; a pre-fence record or a record without `record_kind` aggregates as today (grandfathered)
- [ ] Run → expect GREEN: the summarizer selftest passes in full
- [ ] Extend the review-loop mechanical-gate paragraph: a clean exit additionally requires the round's record to be `record_kind: canonical`; a reconciliation or worker-evidence record can never certify the round (validator-enforced; the prose names the rule and defers the enum to `review-staging`)
- [ ] Extend the review-plan inlined sidecar-schema block with the `record_kind` field (date-fenced required; plan reviews always declare `canonical`) and the coverage-object trigger amended to canonical records (mirroring the authoritative copy in `review-staging`)
- [ ] Extend the execute-plan code-review worker prompt staging sentence: the `.stats.json` sidecar declares `record_kind: canonical` post-fence
- [ ] Extend the rfc-design staging Step 2 sidecar sentence and the review-confluence-doc Step 1 and Step 4 sidecar sentences: version-1 sidecars dated on or after `RECORD_KIND_SIDECAR_MIN_DATE` declare `record_kind: canonical` (the date fence makes a kind declaration mandatory for every producer, so these one-sentence declarations ride this task rather than the deferred disposition matrix)
- [ ] Extend the review-reconciliation Output contract: the durable staged artifact declares `record_kind: reconciliation` and is never eligible to certify a clean exit (one sentence, mirroring the authoritative enum in `review-staging`)
- [ ] Run the interim gate; given the tree at this point, expects `python3 scripts/summarize_review_stats.py --selftest`, `python3 scripts/validate_review_staging.py --selftest`, and `python3 scripts/plan_readiness.py --sweep` all green (the readiness validator inherits the canonical-clean rule through the shared sidecar gate)
- [ ] Commit: `skills: canonical-only clean exit and producer declarations for review records`

### Task 3: record selection helper with overwrite guard and immutable backup

Files:
- `scripts/review_record_selection.py` *(new)*
- `scripts/test_review_record_selection.py` *(new)*
- `scripts/validate_review_staging.py`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`

- [ ] Write the RED suite `scripts/test_review_record_selection.py` with these cases, each self-contained:
- [ ] `test_select_new_record_pair`; given an empty reviews directory and slug `demo`, expects decision `new-record` with the `-r1` Markdown and sidecar paths emitted before any worker could launch
- [ ] `test_select_reuses_same_pass`; given an existing `-r1` pair whose sidecar `source_digest` matches the caller-supplied `--source-digest` of the bytes about to be reviewed and no explicit new-round flag, expects decision `reuse` returning the same `-r1` pair (a worker-lens refresh stays in-round)
- [ ] `test_select_refuses_changed_digest_without_decision`; given an existing `-r1` pair and a caller-supplied `--source-digest` differing from the record's sidecar `source_digest`, expects exit 1 with an error naming the existing record and the two supported actions (rerun with `--explicit-new-round` to allocate the next round, or `backup` for the explicit archival operation), and expects the prior pair byte-identical after the refusal
- [ ] `test_select_allocates_next_round_on_explicit`; given the same differing digest plus `--explicit-new-round`, expects decision `new-round` allocating `-r2` (next free suffix after enumerating existing `-r<N>` records)
- [ ] `test_select_ignores_backup_pairs`; given the same directory plus a `<basename>.backup-<timestamp>.md` and `.stats.json` pair, expects the same next suffix as without the pair (backup-shaped names never inflate the enumeration)
- [ ] `test_select_refuses_orphan_half`; given a directory where only the sidecar of `-r1` exists, expects exit 1 naming the orphaned half and refusing both reuse and allocation until repaired
- [ ] `test_mark_superseded_writes_marker_once`; given a prior record and a successor path, expects the prior file to gain exactly one `Superseded by: <successor>` Metadata line with every finding byte unchanged, a second invocation with a different successor to exit 1, and a matching-successor re-invocation to be idempotent
- [ ] `test_backup_writes_timestamped_pair`; given an existing pair and a permitted same-pass replacement, expects `<basename>.backup-<timestamp>.md` and `.stats.json` copies under the reviews directory, byte-identical to the prior pair, with the backup path printed for the new record's Metadata line `Backup of prior record:`
- [ ] Run → expect RED: `python3 scripts/test_review_record_selection.py` fails (module does not exist yet; the suite collects import errors as failures, nothing passes)
- [ ] Implement `scripts/review_record_selection.py` (standard-library only) with subcommands `select`, `mark-superseded`, `backup` and the guard semantics above
- [ ] Run → expect GREEN: the selection suite passes
- [ ] Add the validator selftest `_selftest_supersession_links`; given a record whose Metadata carries `Supersedes: <prior>`, expects acceptance when the prior file exists and carries the matching `Superseded by:` back-reference, and one actionable error when the link is missing, dangling, or mismatched; run → expect RED then GREEN in the same task
- [ ] Write the contract prose: extend the `review-staging` "Canonical record and supersession" section so every orchestrator runs the selection helper before workers launch, writes only helper-emitted paths, invokes `backup` before any permitted same-pass replacement, and records the backup path in Metadata; add the same requirement to the doing-code-review Steps 2-4 area and one line to the review-loop staging section
- [ ] Run the interim gate; given the tree at this point, expects the selection suite, the validator selftest, and the `CHECK_NO_EM_DASH_ALL=1` em-dash scan over the new files all green
- [ ] Commit: `scripts: review record selection helper with overwrite guard`

### Task 4: backlog capture hygiene check

Files:
- `scripts/scan-public-hygiene.sh`
- `agents/skills/receiving-review/SKILL.md`

- [ ] Add scanner selftest cases for the explicit-paths mode: `--files <path>` over a clean file passes; over a file carrying an absolute home path and a local-pattern hit fails; over a LICENSE.txt carrying a copyright email still passes (the allowlist glob applies in explicit mode too); and a named file outside the default scan roots (for example `docs/history/backlog/draft.md`) is scanned when named explicitly
- [ ] Run → expect RED: `bash scripts/scan-public-hygiene.sh --selftest` fails on the new labels (`--files` does not exist yet)
- [ ] Implement `--files <path>...` on `scripts/scan-public-hygiene.sh`: scan exactly the named files (tracked or untracked) with the same two built-in patterns and the same shared patterns file, applying the standard allowlist globs; exit 1 on any hit, exit 2 on its own errors; no behavior change to the full-tree and `--changed-from` modes. The deny-rule surface stays frozen: the built-in regexes and the shared patterns file remain the only pattern sources, so a tightened rule lands once and reaches every consumer
- [ ] Run → expect GREEN: the scanner selftest passes in full
- [ ] Wire the producer step into `receiving-review` Backlog capture: after composing the backlog item and writing the draft file, run `bash scripts/scan-public-hygiene.sh --files <draft-path>` from the repo root while the draft is still uncommitted; a nonzero verdict stops the capture: fix the draft in place and rerun, never widen or fork the patterns file to make it pass; record the check in the item's source reference
- [ ] Run the interim gate; given the tree at this point, expects the scanner selftest green and the no-em-dash authoring rule respected in the new insertions (the script's legacy em-dash region stays frozen; no whole-file sweep over it)
- [ ] Commit: `scripts: explicit-paths hygiene scan mode wired into backlog capture`

### Task 5: final validation

Files: none (verification only)

- [ ] Run the complete Validation Commands block; expect every line green
- [ ] Verify `git status --short` shows only this plan's declared files as modified or new; any foreign path is reported, never staged
- [ ] Commit any remaining stragglers from Tasks 1-4 (none expected): `skills: review records contract final validation`
