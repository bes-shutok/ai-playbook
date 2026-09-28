# Backlog: emit roundtrip guard VT/FF term unreachable via CLI enumeration

Driving force: code-quality

p79 r2 finding N1 (docs/reviews/2026-09-29-p79-code-review-r2-verification.md): the `[\v\f]\.md$` term in the emit-foreign-candidates roundtrip abort is CLI-unreachable - vertical-tab/form-feed/newline-named candidates under a gitignored reviews dir drop out at the frozen `ls-files` enumeration (git octal-escapes; `_ignored_paths` never unquotes). The guard term is predicate-level only; a pre-existing frozen-surface shape. Either unquote octal-escaped enumeration output before classification or drop the term and document the enumeration-side behavior.
