Status: open
Priority: high
Class: fix-class
Origin class: skills-corpus defect (learn capture completeness, 2026-11-05 harvest pass)

# A long run's early capture passes go stale; nothing re-probes them before the run reports capture complete

## Problem

During the 2026-11-04 parallel fleet, capture passes ran once per boundary mid-run and were repeatedly amended afterward by the same or a peer session: an EXEC entry amended at 18:50Z to cite applicable landing lessons its emission missed (65c0ef5f3), two backlog rows extended at 21:21Z with evidence the earlier capture missed (e4fcf1a87), and a new row filed at 21:38Z for a gap the earlier captures missed entirely (a35cf8fc7). The capture contract has no freshness re-probe: rows and entries written early in a multi-boundary run go stale as the run's own evidence grows, the same-day witnesses are priced as extra passes, and each stale capture risks a parallel session acting on incomplete evidence. `learn` already owns the self-omission rule (an omission by the capture pass is its own skills-corpus candidate); what is missing is the mechanical moment: a re-probe of the run's own earlier captures before capture is reported complete.

## Observed vs expected

Observed: capture artifacts are write-once at their boundary; corrections arrive as separate later commits from whichever session notices.
Expected: learn's completion checklist (or the final boundary's learn invocation) re-probes the run's own earlier capture artifacts against the run's final evidence set and lands dated extensions or the missed row itself before reporting capture complete.

## Evidence (trimmed)

- The three 2026-11-04 amendment commits above (diffs: one entry edit, two row evidence extensions, one new row), all within one evening's fleet window, two of them from the session whose own earlier captures they extend.
- The learn skill's Step 1.8 self-omission rule already names the defect class; the gap is only the re-probe moment and its placement in the run order.

## Suspected root area

`agents/skills/learn/step-completion.md` (the completion checklist) plus the boundary learn contract it serves (the execute-plan light boundary's learn invocation). The fix is a checklist arm with a bounded scope (this run's own artifacts only, never a corpus-wide sweep), priced under the anti-growth rules.

## Ship when

The learn completion checklist carries the re-probe arm (scope: artifacts this run authored, evidence set: this run's final state), and a follow-up multi-boundary run shows the arm executed at least once with a dated extension or a none-found note.
