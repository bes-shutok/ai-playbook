# guidelines: rule-27 Verify-line convention

Cluster: code-quality
Driving force: code-quality

Execution intermediate review (Step 1.2b) backlogged candidate from the finite-string-state-values-need-enum-review-guidance run: rules 20-25 of projects/.ai-playbook/jvm_guidelines.md follow a three-part shape ending in a `**Verify:**` line, while the newly landed rule 27 uses prose + bullets + example with no Verify line. Within whole-file variance (11 of 27 rules carry Verify) and the plan's checklist prescribed the landed shape, so it is not a defect; it breaks the uniformity of the six-rule tail run.

Suggested resolution: in the next guidance-touching change that pays for its own growth, either add a one-line Verify to rule 27 (finite-gauge check style) to match the rules 20-25 shape, or record that recognition rules are Verify-less by design.
