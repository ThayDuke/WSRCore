---
name: wsr-audit
description: Deterministic, read-only WSR quality audit for integrity, structure, minimality, dependencies, resources, and IDE bindings.
---

# WSR Audit

Use `scripts/wsr_audit.py`. Never edit findings automatically.

<!-- START_BLOCK: SCOPE -->
## Scope

- `quick`: changed, staged, and untracked files only.
- `deep`: full tree, skip declared binary/cache classes, run Doctor once when a manifest exists.
- Do not claim repository-wide dependency conclusions in quick mode.
<!-- END_BLOCK: SCOPE -->

<!-- START_BLOCK: CATEGORIES -->
## Categories

- `integrity`: UTF-8, replacement/NUL, Python/JSON parse, coverage.
- `structure`: duplicate rule blocks, hardcoded native paths, alias duplication.
- `minimality`: duplicate Python bodies, unreachable code, oversized symbols.
- `dependency`: unused imports, duplicate declarations, undeclared imports, safe stdlib candidates.
- `resource` and `ide`: mapped from authoritative Doctor gates.
<!-- END_BLOCK: CATEGORIES -->

<!-- START_BLOCK: FINDINGS -->
## Finding rules

Every finding has rule ID, category, severity, confidence, workspace-relative path,
line, evidence, recommendation, and nullable reduction estimates.

Use stable rule IDs. Do not invent severity or thresholds during execution.
Heuristics are never BLOCKER unless the rule explicitly says so.
<!-- END_BLOCK: FINDINGS -->

<!-- START_BLOCK: SCORE -->
## Score

Base 100. Penalty: BLOCKER 25, HIGH 10, MEDIUM 4, LOW 1, INFO 0.
Penalty for one rule is capped at 25. Deep zero coverage is FAIL.
FAIL means threshold finding; WARN means lower-severity finding; PASS means clean.
<!-- END_BLOCK: SCORE -->

<!-- START_BLOCK: OUTPUT -->
## Output

Text prints summary and the first 30 sorted findings.
`--json` prints the complete report matching `wsr-audit-report-v1`.
No timestamp is emitted by default. Findings are deduplicated and deterministically sorted.
<!-- END_BLOCK: OUTPUT -->

<!-- START_BLOCK: GUARDS -->
## Guards

- Read-only by default; no network, dependency install, or auto-fix.
- Preserve `--path`, `--mode`, `--changed`, and `--json` compatibility.
- Use only Python stdlib.
- Stop when source, plan, or adapter contract conflicts.
<!-- END_BLOCK: GUARDS -->
