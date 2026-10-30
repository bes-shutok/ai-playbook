# Backlog: Escape C1 control bytes in release locator paths

Driving force: code-quality
Cluster: release privacy gate diagnostics

scripts/release-privacy-locators.py escape_path (lines 79-95) escapes ESC/ASCII controls/DEL/surrogateescape bytes but a C1 control arriving as valid UTF-8 (U+0080-U+009F, e.g. U+009B CSI) is emitted raw to the terminal. Extend the escape range to code < 0x20 or 0x7F <= code <= 0x9F, with a selftest fixture path carrying C2 9B.
