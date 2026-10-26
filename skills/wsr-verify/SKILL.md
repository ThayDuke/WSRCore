---
name: wsr-verify
description: Verify completion, fixes, builds, and tests with fresh evidence before making success claims.
---

# WSR Verify

No completion claim without fresh, relevant evidence.

Adapted for WSR from `obra/superpowers` verification guidance at commit `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`.

## Boundaries

- Verification is read-only for source files.
- Test-generated caches and reports are allowed only when expected by the repository.
- Never repair failures unless the current task separately authorizes changes.
- Do not trust earlier runs, partial runs, diffs, or another agent's summary as proof.

## Verification gate

1. Translate each claim into an observable acceptance criterion.
2. Select the complete command or inspection that proves that criterion.
3. Run it freshly in the current workspace and environment.
4. Read the full relevant output, exit code, failure count, and skipped checks.
5. Compare actual results against every acceptance criterion.
6. Report success only for criteria proven by evidence.
7. Report failures and unverified areas explicitly.

For a regression fix, prove the test detects the original defect and passes with the correction.

## Output

Report the command, result, covered claim, uncovered scope, and final status.

