# Investigate gains a backlog-wide cluster survey sweep ahead of every anchored pass

[github: https://github.com/admitriev/ai-playbook] Backlog origin: `docs/history/backlog/2026-09-30-investigate-backlog-cluster-survey-mode.md`
Driving force: efficiency

Plan review: docs/reviews/2026-09-30-plan-review-investigate-cluster-survey-anchored-r1.md (r1 verdict ready=yes, zero blocking) (the highest round of the staging series is the authoritative record)

## Gist TLDR

TLDR: every anchored investigate invocation first sweeps the whole open backlog for clusters and pins each discovered roster onto the members' backlog items as an idempotent `Cluster:` header line, so groups are discovered at survey pace with zero new log entries, zero new scheduler duties, and zero state.

## Outcome

The investigate skill's group discovery stops being anchor-limited. Today Stage 1 searches for siblings only of the single item the scheduler hands it, so a cluster whose members never surface as the anchor waits at one-item-per-turn pacing, and late-discovered rosters force plan reconciliations or parallel-session rejections. After this plan, the anchored invocation opens with a bounded survey sweep over the entire open backlog: items sharing a mechanism, surface, or defect class are annotated in place with a `Cluster:` line naming the roster, and Stage 1 then reads that line exactly as it reads a discovered group today.

Settled design questions (the origin's four):

1. **Mode shape - widening Stage 1's scan scope on the anchored invocation.** Not a standalone survey mode (a second invocation surface to wire, schedule, and de-duplicate against the anchored path) and not a new scheduler duty (new cadence state, new park rules, contention with the audit lane's slot). The sweep runs inside the invocation the scheduler already makes, so discovery rides the existing one-investigation-per-turn cadence with no new primitive.
2. **Output contract - annotate, never emit.** The sweep writes no log entries: full entries compete with anchored entries for the dispatch queue and would double-author the same clusters. The roster lands as an additive `Cluster:` header line on each member backlog item (repo-relative sibling paths, the member's own basename excluded); the next anchored pass on any member reads the line in Stage 1 and investigates the group as one unit, recording the roster in the log entry exactly as the existing group path prescribes.
3. **Churn guard - the existing skip rule, extended, plus idempotent writes.** The sweep evaluates only origins that are still ungrouped per the monitor's own skip rule (no intersection with an existing log entry's `Origins:` line, no plans-root plan file); an item whose computed roster is unchanged or absent is left byte-untouched, so steady-state sweeps write nothing.
4. **Bidirectional contract - both Integration Points entries attest the sweep; README unchanged.** The invocation surface does not change (same skill, same one-entry artifact, same hard gates), so the README catalog needs no edit; the investigate/maintenance Integration Points pair gains the sweep attestation on both sides.

## Terms

- **Survey sweep**: the Stage 0 pass over every open top-level backlog item, computing cluster membership per item.
- **`Cluster:` line**: an additive header line on a backlog item, `Cluster: <repo-relative sibling path>` per sibling, written only inside the item's header region (before the first body heading).
- **Ungrouped**: an origin that intersects no existing log entry's `Origins:` line and has no plans-root plan file (the monitor's skip rule, reused verbatim).
- **Anchor**: the single backlog item the invoking turn names (duty (e)'s highest-priority ungrouped open item, or the harvest duty's witnessed-finding item).

## Assumptions

- The sweep is read-mostly: its only writes are `Cluster:` lines, which are advisory rosters for Stage 1, never dispositions, never status changes; a wrong roster is corrected by the next sweep, and no consumer treats the line as authority (the log entry's roster, written only by the anchored investigation, stays the scope of record).
- Bounded cost: the sweep is one similarity read over the open backlog per invocation, the same class of read the anchored Stage 1 already does over the anchor's neighborhood; it adds no network, no sub-agents, and no state.
- The scheduler turn's monitor step needs no text change for the sweep itself (the invocation contract is investigate's own), but duty (e) gains one clause: the turn commits any `Cluster:` annotation writes in the same turn, per the log's write discipline (the annotations are review-corpus-adjacent item edits, so they ride the same turn-commit rule).
- The harvest duty's invocation form (the second consumer form) carries the same sweep for free: it invokes the same skill, and the sweep is part of the anchored pass, not a scheduler-turn-only behavior.

Decision points requiring a grill: none - the origin item prescribes the four questions and this plan answers each from the repo's own precedents (the skip rule, the log-entry artifact rule, the write discipline); the operator's direction was to file and build the fix, and the widening option is the only one that adds no new surface.

### Task 1 - Investigate skill: the Stage 0 sweep

- [x] In `agents/skills/investigate/SKILL.md`, add `### Stage 0: backlog-wide cluster survey (runs on every anchored invocation)` immediately before `### Stage 1: group discovery`: the pass reads every open top-level backlog item in the resolved `backlog_dir`, groups items sharing a mechanism, surface, or defect class (the Stage 1 grouping criteria), skips origins that are not ungrouped (the monitor's skip rule: no log-entry `Origins:` intersection, no plans-root plan file), and for each computed roster of two or more writes one additive `Cluster:` line per sibling into each member's header region (repo-relative paths, the member excluded, idempotent: unchanged rosters never rewrite, no-cluster items never touched). The sweep emits no log entries and changes no status. Stage 1 gains one opening sentence: read the item's `Cluster:` lines as discovered-sibling input before the similarity search. [class: IMPLEMENTATION_REQUIRED] (backfilled 2026-10-01)

### Task 2 - Maintenance skill: the annotation-write duty clause

- [x] In `agents/skills/maintenance/SKILL.md`, duty (e) of the Rolling prompt log duties bullet: append one clause - the invocation carries investigate's Stage 0 survey sweep, and any `Cluster:` annotation writes the sweep performed are committed by the same turn under the log's write discipline (re-read and compare before every write; repo-relative paths only). [class: IMPLEMENTATION_REQUIRED] (backfilled 2026-10-01)

### Task 3 - Bidirectional attestation

- [x] In `agents/skills/investigate/SKILL.md`, the `### With `maintenance` skill` entry: append one sentence - the anchored invocation opens with the Stage 0 survey sweep and its `Cluster:` annotation writes; the scheduler turn commits them and reads the emitted entry exactly as before. [class: IMPLEMENTATION_REQUIRED] (backfilled 2026-10-01)
- [x] In `agents/skills/maintenance/SKILL.md`, the Integration Points section's investigate entry: append one sentence attesting the same sweep from the consumer side (the invocation carries the sweep; annotation writes are committed same-turn). [class: IMPLEMENTATION_REQUIRED] (backfilled 2026-10-01)

### Task 4 - Validation

- [x] All checks in Validation Commands pass from the worktree root. [class: REPOSITORY_TEST] (backfilled 2026-10-01)

## Evaluation Criteria

- The investigate skill carries the Stage 0 sweep with the annotate-never-emit contract, the extended skip rule, and idempotent roster writes; Stage 1 reads `Cluster:` lines.
- Duty (e) carries the same-turn commit clause; both Integration Points entries attest the sweep with no over-claim.
- No new scheduler duty, no new state key, no log-entry emission change, no README change; `agents/skills/maintenance/prompt-templates.md` byte-unchanged.

## Review Scope

Files: `agents/skills/investigate/SKILL.md` (the Stage 0 section, the Stage 1 opening sentence, the maintenance Integration Points entry only), `agents/skills/maintenance/SKILL.md` (duty (e)'s clause and the Integration Points investigate entry only). Contract files referenced read-only: the origin backlog item, the Rolling prompt log duties bullet (duty (e) and the monitor's skip rule), the log's write-discipline rules.

## Validation Commands

Run from the worktree root; every check fails closed:

1. `grep -q "Stage 0: backlog-wide cluster survey" agents/skills/investigate/SKILL.md || { echo FAIL: stage0 missing; exit 1; }` - the sweep section exists (zero hits on main).
2. `grep -qF 'Cluster:' agents/skills/investigate/SKILL.md || { echo FAIL: cluster line missing; exit 1; }` - the roster-line contract is pinned.
3. `grep -q "Stage 0 survey sweep" agents/skills/maintenance/SKILL.md || { echo FAIL: duty clause missing; exit 1; }` - duty (e)'s clause exists.
4. `awk '/^## Integration Points/{f=1} f && /^## /&& !/^## Integration Points/{f=0} f' agents/skills/investigate/SKILL.md | grep -q "Stage 0 survey sweep" && echo ip-ok || { echo FAIL: investigate IP attestation missing; exit 1; }` and the mirrored maintenance-side pin: `awk '/^## Integration Points/{f=1} f && /^## /&& !/^## Integration Points/{f=0} f' agents/skills/maintenance/SKILL.md | grep -q "Stage 0 survey sweep" && echo ip2-ok || { echo FAIL: maintenance IP attestation missing; exit 1; }`.
5. `git diff --quiet main -- agents/skills/maintenance/prompt-templates.md README.md || { echo FAIL: out-of-scope file touched; exit 1; }` - the blueprints and README are byte-unchanged.
6. `grep -c "Stage 0" agents/skills/investigate/SKILL.md | xargs test 1 -le` - the section name is pin-once (a duplicated stage heading would drift the anchors); equivalently `[ "$(grep -c '^### Stage 0' agents/skills/investigate/SKILL.md)" -eq 1 ] || { echo FAIL: stage0 duplicated; exit 1; }`.
7. `bash scripts/scan-public-hygiene.sh && bash scripts/check-no-em-dash.sh added-lines --base main || { echo FAIL: gates; exit 1; }` - both exit 0.

## Completion record (backfill 2026-10-01)

This section is an explicitly marked backfill, written 2026-10-01; it is not a contemporaneous completion record. The record written at execution time was lost with the executing worktree's gitignored reviews directory: the run's transfer-out migrated only closeout files, not the review pair, so the plan header's cited r1 receipt `docs/reviews/2026-09-30-plan-review-investigate-cluster-survey-anchored-r1.md` has no bytes on disk (no `survey-anchored` file exists under `docs/reviews/` on any branch). A later reader of this archive therefore reads this record, not the lost original.

The re-verification evidence substitutes for the never-transferred contemporaneous record, taken from the origin item's recorded audit (`docs/history/backlog/2026-09-30-investigate-backlog-cluster-survey-mode.md`, Status line, 2026-09-30): the run was executed and landed with exec review r1 ready=yes zero blocking; all seven of this plan's Validation Commands re-ran green on main in the 2026-09-30 audit session; and the exec squash commit (main 85122e7e) touches exactly the two in-scope files, `agents/skills/investigate/SKILL.md` and `agents/skills/maintenance/SKILL.md`.

This write is licensed as an explicitly-marked backfill under the plans skill's amended archive-step no-rewrite exception (a marked backfill completion record plus per-checkbox markings, allowed only when contemporaneous evidence is documented in the record); the doc-registry's completed-history write check observes the licensed marking. The plan header's `Plan review:` label form (not the generic `Plan review record:` form) is the cited-receipt label this backfill covers; the header's review link still points at the staging series it cited and the certified-review-digest trail is untouched. The five task checkboxes above are checked, each carrying a per-checkbox marking appended to the line.
