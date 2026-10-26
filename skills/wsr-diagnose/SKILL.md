---
name: wsr-diagnose
description: Diagnose bugs, failures, and unexpected behavior by proving root cause before proposing or applying fixes.
---

# WSR Diagnose

Find the root cause before changing production code.

Adapted for WSR from `obra/superpowers` systematic debugging at commit `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`.

## Boundaries

- Diagnosis is read-only by default.
- Instrumentation or source edits require current-task approval.
- Never treat a hypothesis as a confirmed cause.
- Preserve unrelated user changes.

## Workflow

1. Capture the exact symptom, environment, and complete error output.
2. Reproduce consistently, or state why reproduction remains unavailable.
3. Inspect recent changes and trace inputs across component boundaries.
4. Compare failing behavior with the nearest working example.
5. State one falsifiable hypothesis and test it with the smallest probe.
6. Record evidence confirming or rejecting that hypothesis.
7. Identify the root cause before proposing the smallest corrective change.

After three failed corrective attempts, stop and question the architecture with the user.

## Handoff

- For an approved code change, use `wsr-tdd` when automated testing is practical.
- Before any success claim, apply `wsr-verify`.
- Report symptom, evidence, root cause, proposed correction, and remaining uncertainty.

