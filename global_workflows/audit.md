---
description: Run deterministic, read-only WSR integrity, structure, minimality, dependency, resource, and IDE audits
---

# /audit

Default: read-only quick audit of changed files.

`python scripts/wsr_audit.py --mode quick`

Deep audit is explicit:

`python scripts/wsr_audit.py --mode deep --json`

Optional filters:

- `--path PATH`
- `--category NAME`
- `--fail-on blocker|high|medium|low`
- `--explain RULE_ID`

Report FAIL before WARN. Do not auto-fix. Do not write a ledger.
Use `--json` for the complete machine-readable report.
