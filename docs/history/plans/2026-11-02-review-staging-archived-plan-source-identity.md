# Plan: Archive-aware source resolution for review records after plan archival

Backlog origins (scope of record):
- docs/history/backlog/2026-11-02-review-staging-archived-source-path.md

Driving force: code-quality

Plan review record: the staging series .ai-playbook/reviews/2026-11-02-plan-review-review-staging-archived-plan-source-identity-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)

Execution budget: 2h total, largest task 1h

Authoring claim: review-staging-archived-plan-source-identity.md (session sess_175f4067-23d2-4a64-b802-b1ce6674e2d1)

## Terms

- archived twin: the completed-archive copy of a plan under the facts-resolved completed directory of the plans layout (the `plans_completed_dir` facts key, conventional default `docs/history/plans/completed/<basename>`), produced by the Plan Lifecycle archive move (a move that preserves bytes). The twin candidate is a regular file only; a directory-shaped archive keeps today's refusal shapes (known limitation).
- plans layout: the facts-resolved plans directory (`plans_dir`, conventional default `docs/history/plans/`). Only a recorded path whose parent resolves to the plans layout gets a twin candidate; every other recorded path (backlog rows, source files, documents) is inert to the resolution.
- archive-twin resolution: the shared compare-then-resolve helper this plan adds to `scripts/validate_review_staging.py`: for an in-scope relative recorded path it appends the completed twin as a trailing candidate (unconditionally; the consumers' existing first-existing-candidate semantics make the append outcome-equivalent to an existence-gated append, without probing inside the helper, with one priced exception: the linked-round consumer's loop continues past a present-but-non-dict primary, so this plan adds the one-line first-existing stop to `_coverage_linked_round` - output-identical over today's candidate list, whose second candidate is only the working-directory duplicate - so a present primary, any parse result, precludes twin substitution and twin evidence enters only when no earlier candidate exists). The candidate is derived from a path normalized within the repository root and confined under it (a twin that would escape the repository is not produced; the record is unaffected). Every digest-bearing consumer still binds the resolved bytes to the record's recorded digest, so the evidence bar is unchanged; a missing twin and a bytes-changed twin both keep today's refusal shapes.
- identity path: the repository-relative pre-archive plans-root path a review record binds as its plan identity (`extensions.plan_identity`, the legacy `URL or Artifact` field, and the identity token minted into identity-qualified review filenames). Archival never rewrites identity: records keep citing the original path, and the resolution derives identity from that original path even when the bytes come from the twin.
- local-equivalence attempt: a `coverage.attempts[]` entry with `execution_mode: "local"` and `contributed_coverage: true`, which the coverage contract admits only with `prompt_scope` plus an existing artifact and `.stats.json` sidecar pair (`validate_coverage_contract`, the `coverage local-mode attempt` error family).
- stale-source gate: the `main()` digest comparison that recomputes the source digest from the bytes the source flag resolved and rejects a mismatch against the sidecar's recorded `source_digest`.

## Why

Plan archival moves the reviewed plan out of the plans root, and historical plan-review records keep pointing at the former plans-root path in two places: the `coverage.attempts[].artifact` and sidecar links, and the `--source-plan` operand a closeout re-validation passes. The done landing sweep requires the referenced artifact to exist, so the closeout refused on otherwise-superseded historical evidence (the 2026-11-02 witness: review r10 of the Codex continuation plan refused after its source moved to `docs/history/plans/completed/`; the hand repair retargeted the artifact references to the completed path and the sweep passed with the original `source_digest` intact). The hand repair is a per-record workaround, not a contract: each not-yet-retargeted record re-fuses the next closeout that walks it.

## Gist & Examples

TLDR: the staging validator gains a shared archive-twin resolution helper so a plan-review record whose source plan has archived resolves its coverage artifact links and its `--source-plan` operand through the completed twin, scoped to the plans layout via the facts keys with identity staying the pre-archive path and every digest, parse, and missing-source refusal intact, for code-quality.

Before: a plan-review record citing `docs/history/plans/<plan>.md` in a coverage attempt fails the artifact-exists check once the plan archives to `docs/history/plans/completed/<plan>.md`; a `--source-plan docs/history/plans/<plan>.md` re-validation exits tool-error with `source file not found` after archival; the only remedy is hand-retargeting each historical record, which rewrites durable history one record at a time.

After: the coverage link candidates include the completed twin for in-scope paths, so the existing artifact/sidecar pair check passes on unchanged reviewed bytes without touching the record; the `--source-plan` arm resolves the twin before the not-found refusal (kind-gated to `--source-plan`), reads the digest evidence from the twin's bytes, names the resolved twin path in the stale-source hint, and keeps deriving plan identity from the original pre-archive path; a twin whose bytes changed fails the stale-source gate exactly as a drifted primary does, and a missing twin still refuses.

Edge cases: a plan whose archive pass carried the promoted-backlog disposition body edit hashes differently at the twin, so its historical records keep the stale-source refusal (the origin's own continuity bar: unchanged reviewed bytes resolve, mismatched sources refuse); a recorded path outside the plans layout gets no twin candidate because the scoping gate enforces the plans layout (a coverage link citing a landed backlog row stays inert even though `docs/history/backlog/completed/` exists); a `..`-bearing recorded value derives no twin outside the repository root; a directory-shaped archive keeps today's refusal; a record created after archival already binds the completed path and never enters the resolution (its primary path exists).

## Outcome

A plan-review record whose source plan has archived validates end to end without any record rewrite: coverage attempt links and the `--source-plan` operand resolve through the completed twin, identity stays the pre-archive path, and every existing refusal shape survives.

- Coverage attempt artifact and sidecar pairs (attempts, replacement, and inherited entries alike) resolve through the archived twin; the local-equivalence evidence bar (existing pair, parseable sidecar JSON) is unchanged.
- The `--source-plan` arm resolves the twin before its not-found refusal; the recomputed digest binds the twin's bytes, the stale-source hint names the resolved twin path, and the identity derivation keeps the original path.
- The archive move's own contract is unchanged: no archive-time record relocation, no snapshot surface, no new gate, validator, or output line.

Gate delta: none. No gate, ledger, refusal surface, validator exit, or output surface is added or removed; the change widens path resolution inside the existing checks, priced by the origin row's witnessed closeout refusal. The demotion-adjacent read: the hand-retarget workaround class retires (records stop needing post-archive edits), and nothing else changes surface count.

## Assumptions

- Option selection: archive-time reference relocation is rejected (it rewrites durable records corpus-wide and races every record produced after the sweep read; the serving entry's rejected alternatives price the manual form); an immutable source snapshot is rejected (the completed archive already is the byte-preserving snapshot; a second copy adds a surface without closing the gap); archive-aware validator resolution is selected as the smallest option (no record rewrites, no new surface, existing checks keep their verdicts).
- Plans-layout scoping and facts keys: the twin candidate is produced only for recorded paths whose parent is the facts-resolved plans directory, and the completed directory is the facts-resolved `plans_completed_dir` (the validator's existing `facts_paths` import is the in-file precedent; the conventional defaults are the fallbacks). This is the enforced containment invariant, not an assertion: without the scoping gate the parent-sibling derivation would fire for `docs/history/backlog/completed/`, which exists in this repository (r1 F3 verified on disk).
- Digest scoping: the collision-safety backstop lives on the source-flag arm only, where the recomputed digest binds the resolved twin's bytes. The coverage arms (attempts, replacement, inherited) bind existence plus parseable sidecar JSON, exactly as they do for primary paths today, so a drifted twin passes the coverage bar by design; that is the unchanged evidence bar, not a new acceptance. Task 3's doc paragraphs state the same scoping so no surface imports the over-claim (r1 F5).
- The disposition-edit class keeps refusing by design: the origin's continuity disposition requires the guard to pass on unchanged reviewed bytes, and a disposition-edited archive is changed bytes at the record's bound digest. Widening that would weaken the stale-source gate; explicitly out of scope.
- The coverage-attempt arm adds existence resolution only (the pair must exist and the sidecar must parse, as today); it does not add a digest comparison that does not exist today, so the evidence bar is byte-identical.
- Fixture mechanisms the pins name: the twin pins run under the battery's established chdir fixture pattern (save, chdir into a subdirectory of the battery root, restore in finally) with placeholder basenames that never collide with the live tree, and the identity pin builds a throwaway git repository inside the battery root so `repository_root` resolves and the three identity comparisons actually fire (r1 F6, F7).
- The witness incident's hand-repaired r-series binds the completed path as its primary and never exercises the twin; it stays regression context only. The live twin-exercising probe is the Ship-when fixture step, not a task.

Decision points requiring a grill: identity derivation stays bound to the pre-archive path rather than introducing an identity-equivalence comparison - taken deliberately, decision source this plan's Terms and Task 2 pricing (deriving identity from the original path keeps the record-side contract untouched, an equivalence comparison would widen every identity check to justify one call site), 2026-11-02, affected section Task 2; the disposition-edit refusal retained rather than special-cased - decision source the origin's continuity disposition text (pass on unchanged reviewed bytes), 2026-11-02, affected section Assumptions.

## Standing constraints

- Script changes stay in `scripts/validate_review_staging.py` (including its embedded selftest battery); no other validator, gate, or script is touched.
- Doc changes stay in the three named surfaces (`agents/skills/review-staging/SKILL.md`, `agents/skills/plans/SKILL.md` archive move bullet, `agents/skills/done/SKILL.md` final gate region); each states only what the code now does.
- The pins suite must stay green: `scripts/check_maintenance_pins.sh` pins validator text, so any line a pin tokenizes is checked before landing (see Validation Commands).

## Evaluation Criteria

**Quality dimensions:**

- Correctness: an archived-plan fixture passes the coverage attempt check and the `--source-plan` re-validation; the drift mutant (twin bytes changed under the record's digest) dies at the stale-source gate naming the resolved twin path; the missing-twin mutant (twin absent) still refuses.
- Contract fidelity: refusal shapes are byte-stable; no new error string, output line, or exit code enters the contract.
- Compatibility: records binding existing primary paths never enter the resolution; non-plan record kinds and out-of-layout paths are inert.

**Done when:**

- The origin row's scope arms are implemented and pinned: the eight pins of the canonical inventory (coverage-twin, unparseable-twin-sidecar, plans-layout-scoping, source-flag-twin, drift-mutant, missing-twin, identity-stability, file-shaped-twin) pass in the embedded selftest battery, each with its owning task checkbox.
- The three doc surfaces state the resolution and are verified by reading each against the behavior it documents.
- `python3 scripts/plan_readiness.py <plan>` exits 0 over the final review series.

**Ship when:**

- Two-step probe: (1) a closeout-shaped fixture record still citing the pre-archive plans-root path (primary absent) validates end to end through the twin resolution; (2) the hand-repaired witness r-series still validates as regression context (operations follow-up, owner: the next closeout that walks those records).

## Validation Commands

```bash
python3 scripts/validate_review_staging.py --selftest
bash scripts/check_maintenance_pins.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-11-02-review-staging-archived-plan-source-identity.md
```

## Design Invariants

- Identity is never rewritten: records keep citing the pre-archive path; no task edits a stored record's identity fields.
- The twin candidate exists only for recorded paths inside the plans layout, under the facts-resolved completed directory, normalized and confined within the repository root; no absolute path, no path outside the layout.
- Every existing refusal string and exit code keeps its shape; the resolution only adds resolution, never acceptance, and adds no output line.

## Review Scope

**Explicit must-fix:**

- `scripts/validate_review_staging.py` (Task 1): the archive-twin resolution helper (facts-key scoping, normalization, confinement), the `_coverage_link_paths` candidate arm, and the `_coverage_linked_round` first-existing stop (the Terms-priced exception).
- `scripts/validate_review_staging.py` embedded selftest (Task 1): the coverage-twin pin, the unparseable-twin-sidecar pin, and the plans-layout-scoping pin.
- `scripts/validate_review_staging.py` (Task 2): the `--source-plan` not-found arm's twin resolution (kind-gated), identity derivation from the original path, and the stale-source hint threading.
- `scripts/validate_review_staging.py` embedded selftest (Task 2): the source-flag-twin, drift-mutant, missing-twin, identity-stability, and file-shaped-twin pins.
- `agents/skills/review-staging/SKILL.md` (Task 3): the coverage contract's archive-aware resolution paragraph.
- `agents/skills/plans/SKILL.md` (Task 3): the archive move bullet's one-line records-resolution note.
- `agents/skills/done/SKILL.md` (Task 3): the final gate region's one-line resolution note.

**Production code:** the twin-resolution helper, the coverage candidate arm, and the source-flag resolution arm in `scripts/validate_review_staging.py`.

**Tests:** the embedded selftest battery's new pins (eight total).

## Tasks

### Task 1: The archive-twin resolution helper and the coverage candidate arm

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/validate_review_staging.py`

Primary class anchors:
- `_coverage_link_paths` in `scripts/validate_review_staging.py`
- `_coverage_artifact_exists` in `scripts/validate_review_staging.py`
- `_coverage_linked_round` in `scripts/validate_review_staging.py`
- `facts_paths` in `scripts/validate_review_staging.py`

- [ ] The twin-resolution helper delivers in-scope twin derivation: given a relative recorded path whose parent resolves to the facts-resolved plans layout, expects the completed twin (facts-resolved `plans_completed_dir` + basename) appended as the trailing candidate; given an absolute recorded path, expects no twin candidate [class: IMPLEMENTATION_REQUIRED]
- [ ] The twin-resolution helper delivers the containment refusals: given a recorded path outside the plans layout (a backlog row), expects no twin candidate; given a `..`-bearing value whose twin would escape the plans layout or the repository root, expects no twin candidate (the confinement arm) [class: IMPLEMENTATION_REQUIRED]
- [ ] `_coverage_link_paths` delivers the unconditional trailing append: given an in-scope relative recorded path, expects the twin appended last without any existence probe inside the helper; given a recorded path with an existing primary candidate, expects outcome equivalence (the primary resolves first; the twin resolves only when primaries are absent) across the attempts, replacement, and inherited consumers [class: IMPLEMENTATION_REQUIRED]
- [ ] The coverage consumers keep their evidence bar over the twin: given a local-mode attempt whose artifact and sidecar live only at the completed twin, expects the existing artifact-exists and sidecar-parses checks to pass with today's error vocabulary [class: IMPLEMENTATION_REQUIRED]
- [ ] The linked-round consumer keeps its priced stop and the parse guard stays byte-stable: given a present-but-non-dict primary sidecar, expects the first-existing stop to keep today's verdict (the twin resolves only when no earlier candidate exists, per the Terms-priced exception); given a twin sidecar that does not parse, expects the same sidecar error as today [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED: the coverage-twin pin fails against the current validator (the twin shape is unresolved today) [class: REPOSITORY_TEST]
- [ ] Write minimal implementation: the scoping helper (facts keys, normalization, confinement) and the `_coverage_link_paths` append [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the coverage-twin pin; the unparseable-twin-sidecar pin and the plans-layout-scoping pin hold GREEN before and after (byte-stable refusal regression guards) [class: REPOSITORY_TEST]
- [ ] Commit: `fix: resolve coverage attempt links through the completed archive twin` [class: IMPLEMENTATION_REQUIRED]

Evidence: the new pins run under the battery's chdir fixture pattern inside the battery root with non-colliding placeholder basenames (no probe touches the live tree); pins red before the fix where RED is claimed, green after; the battery passes; a record binding an existing primary path produces byte-identical validation output.

### Task 2: The source-flag twin arm with identity stability

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/validate_review_staging.py`

Primary class anchors:
- `main` in `scripts/validate_review_staging.py`
- `normalize_plan_path` in `scripts/validate_review_staging.py`
- `_SOURCE_PATH_FOR_ERROR` in `scripts/validate_review_staging.py`

- [ ] `main` delivers the source-flag twin arm, kind-gated to plan: given `--source-plan` naming a missing plans-layout path whose completed twin exists (a regular file), expects the bytes read from the twin and the stale-source gate to bind those bytes; given `--source-doc` or `--source-record`, expects no twin resolution (today's refusal unchanged) [class: IMPLEMENTATION_REQUIRED]
- [ ] The twin refusals keep today's shapes: given a twin whose bytes hash differently from the sidecar's `source_digest`, expects the existing stale-source refusal with the hint naming the resolved twin path; given a missing twin, expects today's `source file not found` tool error unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Identity stability: given the twin resolution fired, expects plan identity derivation (`normalize_plan_path`, the filename identity-token comparison, and the `extensions.plan_identity` comparison) to use the original pre-archive operand path while the stale-source hint carries the resolved twin path, so an identity-qualified record and its sidecar validate exactly as they did pre-archive [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED: the source-flag-twin pin, the drift-mutant pin, and the identity-stability pin fail against the current validator [class: REPOSITORY_TEST]
- [ ] Write minimal implementation: resolve before the not-found refusal; split the bytes source and the hint path from the identity source [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the three RED pins; the missing-twin pin and the file-shaped-twin pin hold GREEN before and after (byte-stable refusal regression guards) [class: REPOSITORY_TEST]
- [ ] Commit: `fix: resolve the source-plan operand through the completed archive twin with identity stability` [class: IMPLEMENTATION_REQUIRED]

Evidence: the identity-stability pin builds a throwaway git repository inside the battery root so `repository_root` resolves and the three identity comparisons actually fire, and documents the semantic decision (naming the Terms pricing of identity derivation over an equivalence comparison); the battery passes; a primary-path invocation produces byte-identical output.

### Task 3: Doc-surface alignment and full-gate verification

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/done/SKILL.md`

Primary class anchors:
- `validate_coverage_contract` in `scripts/validate_review_staging.py`

- [ ] The review-staging coverage contract states the archive-twin candidate arm scoped to the plans layout via the facts keys, with the evidence-bar scoping (existence plus parse on the coverage arms, digest binding on the source-flag arm) stated explicitly [class: IMPLEMENTATION_REQUIRED]
- [ ] The plans archive move bullet and the done final gate region state the resolution: the archive bullet gains one line stating that records citing the pre-archive path resolve through the completed twin and that no archive-time record relocation happens; the done gate region gains one line naming the resolution at re-validation [class: IMPLEMENTATION_REQUIRED]
- [ ] Pins-suite reconciliation: given the pins suite tokenizes validator and skill text, expects `scripts/check_maintenance_pins.sh` exit 0 after the edits, with any newly pinned line added only if a pin's grammar demands it (the default is no pin change) [class: REPOSITORY_TEST]
- [ ] Full readiness gate over the final assembled series exits 0 [class: REPOSITORY_TEST]
- [ ] Commit: `docs: state the archive-aware source resolution on the three contract surfaces` [class: IMPLEMENTATION_REQUIRED]

Evidence: each doc surface read against the behavior it documents (coverage contract ↔ the Task 1 arm with the digest scoping; archive move ↔ the no-relocation invariant; done gate ↔ the Task 2 arm); pins suite green; `python3 scripts/plan_readiness.py <plan>` exit 0 over the final series.
