# Loss-flag coverage suggestions (exec review r1, interrupted-manifest-gitignored-witness-gap)
Cluster: docs/history/backlog/2026-11-09-operator-directed-loss-unwitnessed-flag-partitions.md

Driving force: code-quality
Date filed: 2026-11-09
Source: Phase 3 execution review r1 suggestions (correctness + spec lenses) for docs/history/plans/2026-11-09-interrupted-manifest-gitignored-witness-gap.md

## Body

Two non-blocking coverage suggestions from the exec review, captured rather than fixed in-run:

1. No behavior cell exercises `--operator-directed-loss` against the reprint arm (already-dispositioned) or the racer arm (CAS loss); both interactions are usage-declared and structurally inert (the reprint return precedes flag logic; the racer reprints the existing record), and no Task 1 checkbox required them.
2. The usage-declares test asserts phrases anywhere in `lib._usage()`; relocating the declaration out of the disposition-manifest entry would keep it green — anchoring assertions to the sliced disposition-manifest entry would harden placement.

Neither affects current behavior; the pinned contract (reason-only flip, inert notice, byte-identical unflagged pins) is covered.
