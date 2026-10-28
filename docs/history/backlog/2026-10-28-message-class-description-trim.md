# Trim captured description in Agent rate-limit class labels

Driving force: code quality
Cluster: friction-audit-quant

**Problem:** the new `_message_class` recognized-form path keeps the captured description verbatim, so `[1302][ desc ]` and `[1302][desc]` remain distinct singleton classes — pre-existing fragmentation the digit-run normalization already fights elsewhere.

**Witness:** intermediate review of plan `docs/history/plans/2026-10-25-friction-audit-quant-message-class-normalization.md` Task 1 (2026-10-28, backlogged-candidates verdict).

**Direction:** strip the captured description in the recognized-form branch of `_message_class` in `scripts/friction_audit_quant.py`; verify 1302/1308 aggregation still holds.
