# Closeout-suite prose residuals (r5 review, deferred family)

Status: open
Priority: low
Cluster: closeout-guard review-residual trio follow-ups
Filed: 2026-11-05, r5 address pass of the closeout-clobber-guard-review-residual-trio execution (record `.ai-playbook/reviews/2026-11-05-closeout-clobber-guard-review-residual-trio-code-review-r5.md`; deferred per the r4 manifest reflection's pre-registered r5 exit policy - prose-vs-code drift class defers to durable rows, r5 is the exit round)

## Residuals

- R-E (r5 F5, contract-docs, `documentation#prose-strip-set-omits-xdg`): the `_StripsHostGitEnv` class docstring's strip-set clause ("save and strip inherited GIT_* variables") omits the `XDG_CONFIG_HOME` strip the code performs since 19ad1b3a2; the same omission recurs in `BaselineClobberGuardTest`'s setUp prose (~line 10731). Remedy: widen the contract clause to "save and strip inherited GIT_* variables and XDG_CONFIG_HOME, restore on cleanup" (and mirror in the setUp prose).
- R-F (r5 F6, contract-docs, `documentation#prose-head-equal-fixture-mismatch`): the HEAD-equal deletion-arm pin's docstring says "(delivered unknown here)" but the fixture passes a known non-matching 40-hex stub (`{self.REL: "f" * 40}`), which is the stronger witness (it catches a delivered-or-head fold mutant). Remedy: correct the parenthetical to name the known-non-matching-stub shape and why it is discriminating; keep the fixture.

## Witness

r5 record findings F5-F6 (worker contract-docs, fresh-adversarial round over digest e39a369aeebaa63b7b1484b255a8557be4438133cec255f62e7981b88f75fc93). Sibling row: docs/history/backlog/2026-11-05-fixture-hermeticity-completeness-residuals.md (same round's hermeticity-completeness family), plus docs/history/backlog/2026-11-05-closeout-guard-teardown-attribution-comment-pointer.md (r3's deferred prose pointer).
