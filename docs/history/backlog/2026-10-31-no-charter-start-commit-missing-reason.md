# no-charter start-commit missing evidence refusal is misattributed

Driving force: output fidelity (specific refusal required by the plan's preservation criterion)

When the newest binding done-run manifest lacks a parseable `start_commit` while an older binding supplies one, the arm refuses as "branch moved past the recorded start commit (branch <oid> != start commit None)" though the branch did not move. Refuse with a specific "manifest <name> carries no parseable start_commit" line. Origin: intermediate review round 4 finding, execute-plan run 2026-10-31 (preservation holds; only the reason is wrong).
