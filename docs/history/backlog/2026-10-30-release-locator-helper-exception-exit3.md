# Backlog: Map unexpected release-privacy-locators failures to tool-error exit 3

Driving force: code-quality
Cluster: release privacy gate diagnostics

An unhandled helper exception (e.g. UnicodeEncodeError on a non-ASCII path under a non-UTF-8 stdout encoding) exits 1 and masquerades as a privacy hit with "no locators derivable" (scripts/release-privacy-locators.py:162); only fatal() paths exit 3. Wrap the main parse loop so unexpected exceptions exit 3.
