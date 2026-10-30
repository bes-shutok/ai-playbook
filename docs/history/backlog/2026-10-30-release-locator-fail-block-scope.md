# Backlog: Scope release locator parsing to FAIL: files block rows

Driving force: code-quality
Cluster: release privacy gate diagnostics

scripts/release-privacy-locators.py parses every stdout line, not only FAIL-block rows (helper line ~156). Identical behavior with the frozen scanner today, but a future stdout addition shaped path:digits: would yield a non-FAIL-row locator; the release plan Terms define locators as FAIL-row-derived. Gate the row parser to the FAIL: files block.
