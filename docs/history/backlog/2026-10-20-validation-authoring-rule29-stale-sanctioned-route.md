# validation-authoring-rules.md rule 29: stale "until a sanctioned route lands"

- **Filed:** 2026-10-20, at the Task 4 boundary of `corrections-chain-operator-ack-end-to-end`
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** documentation drift
- **Class:** fix-class
- **Driving force:** primary: documentation drift; secondary: simplification (an unclassified-relocation hop now has a sanctioned operator-acked route, so the fresh-round premise is false).
- **Skill/step:** `agents/skills/plans/validation-authoring-rules.md` rule 29
- **Dedup probe:** r1 contract-docs lens confirmed the row shape gap; classification bullets added at Phase 3 close.
- **Concern:** plans/validation-authoring-rules.md rule 29 still sends mechanical hash/reference corrections from relocations "until a sanctioned route lands"; the corrections-chain operator-ack plan (docs/history/plans/2026-10-18-corrections-chain-operator-ack-end-to-end.md, landed 2026-10-20) is that sanctioned route, so the clause's premise is false and a reader misses the now-available zero-round path. Conservative fresh-round behavior remains safe; this is missed-simplification drift only.
- **Cluster:** none.
