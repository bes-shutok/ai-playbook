Tracked rolling log of ready-to-dispatch plan-creation prompts, most urgent first.

Standing rules:

- Order: entries sit most-urgent-first; a new entry inserts at the urgency position it merits, judged when it is written.
- Prune rule: an entry is removed when its plan file exists in the plans root.
- Freeze rule: when authoring for an entry has started (a live authoring claim file keyed to the entry slug or one of its origins under the tmp authoring-claims directory, live meaning its `updated:` fresher than one cadence period per the `G1a` discovery arm's bound (a stale claim taking the takeover path instead of freezing), or a live authoring worktree or branch for its plan), the entry is marked frozen before any further log processing: a `Frozen:` line naming the witness and date goes directly under the entry's heading. A frozen entry accepts no origin additions, no prompt rewrites, no repositioning, and is never a dispatch candidate; the mark is removed when the authoring aborts without a plan file in the plans root (the entry reopens), and the entry is pruned outright per the prune rule when its plan file lands.
- Not a backlog item: never cite this file as a plan's Backlog origin.
- Writes are targeted section edits (an entry's own section), never a whole-file rewrite from a stale read.
- Before every write, re-read the file and compare it against the read the edit was prepared from; any difference is drift: retry once from the fresh read, then attempt a pure append of the entry at the end of the file (conflict-free under the targeted-edit rule); only when that append also fails the drift check, abort and report the full intended entry text in the turn output as the fallback record; the next write attempt re-emits from that record instead of re-running the investigation.
- Every log write is committed in the same turn that performs it.
- Entries carry repo-relative paths only and no personal or machine-specific data.
- An entry is a prompt for a later authoring turn; the write turn never executes or dispatches its payload.

Entry template (one section per entry):

```
## <short-slug>

Added: <date and provenance>

Origins:
- docs/history/backlog/<origin>.md

Urgency: <judgment: class, witness, relative queue position>

Prompt: <full ready-to-dispatch authoring prompt payload>

Rejected alternatives:
- <one line per rejected alternative, with the reason>
```

## nested-git-debris-registration

Added: 2026-10-04, investigate pass on the operator-reported git-root incident (two same-turn origin rows, one incident chain; queue empty, first position)

Origins:
- docs/history/backlog/2026-10-04-nested-git-debris-root-registration.md
- docs/history/backlog/2026-10-04-untracked-root-debris-detection-gap.md

Urgency: moderate - the scanner symptom is user-visible and was witnessed twice in one morning (a stale root registration warning, then re-detection at the preserve location), and the live remedy (the .git-deactivated rename) is already applied by hand; what remains is giving the disposition rule a durable repo home, adding the presence probe, and narrowing the classifier's reporting; queue empty, so this sits first

Prompt: Author a plan that (1) gives the debris-disposition rule a repo home: relocating nested-repository debris disarms the embedded .git first (rename to .git-deactivated, witnessed 2026-10-04 on docs/tmp/done-session/flare-20261004-root-debris/h with contents byte-preserved) and records the scanner-side remedy for an already-dangling registration (remove the stale root mapping in the scanner's version-control settings; the gitignored .idea/vcs.xml is an advisory repo-side check only); the plan's archaeology picks the home among the candidates that own foreign-material disposition today (the done skill's dirty-state arm, the maintenance skill text, or a pin); (2) adds the missing-complement presence probe: a done-sweep or maintenance arm listing untracked non-ignored top-level entries, adjudicated against a small allowlist, so debris presence surfaces in a routine turn; (3) narrows the classifier's reporting without softening it: keep the fail-closed OUTCOME: indeterminate contract (introduced by the primary revert-set adjudication landing 1abfaa32) but report every path attempted before the collection failure, not only the first, and add a nested-repository fixture to its selftest.

Rejected alternatives:
- Delete nested-repo debris outright on discovery: rejected, irreversible destruction of foreign peer material against the record-only doctrine (witnessed disposition preserved contents under docs/tmp/done-session/flare-20261004-root-debris/)
- Keep the intact move without disarming .git: rejected, the operator reported the same registration symptom at the preserve location minutes after the intact move (flare record addendum 2026-10-04 07:41, docs/tmp/done-session/flare-20261004-dirty-main.md)
- Fix scanner-side only (IDE exclusions, no repo change): rejected, scanner configuration is machine-local and gitignored, so the repo can neither enforce nor observe it; the repo-side witnessed remedy is the .git-deactivated rename (docs/history/backlog/2026-10-04-nested-git-debris-root-registration.md)
- Make the classifier skip nested repositories: rejected, that silences the exact witness that surfaced the debris; keep fail-closed indeterminate with full enumeration instead (scripts/revert_set_classifier.py)
- Rewire existing gates (hygiene scan, validators) to flag untracked presence: rejected, their contracts scan content over changed or tracked scope, so presence detection is a new complement and not a widening (scripts/scan-public-hygiene.sh)

