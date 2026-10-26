---
name: wsr-tdd
description: Implement approved features, bug fixes, and behavior changes through a focused red-green-refactor cycle.
---

# WSR TDD

Use tests to define behavior before production implementation.

Adapted for WSR from `obra/superpowers` TDD guidance at commit `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`.

## Authority

- Loading this skill never grants write permission.
- Production and test edits require current-task approval under WSR.
- Preserve existing user work; never delete pre-existing code merely to recreate a red state.

## Cycle

1. Define one observable behavior and the smallest suitable test.
2. Add the test and run it before production changes.
3. Confirm RED: failure occurs for the expected behavioral reason.
4. Add the minimum production change needed for that test.
5. Confirm GREEN with the focused test.
6. Run the relevant regression suite.
7. Refactor only when behavior remains green and scope stays approved.
8. Apply `wsr-verify` before claiming completion.

If production code already exists, use a regression test that exposes the defect.

Generated code, throwaway prototypes, or configuration-only changes may use an agreed alternative verification path.

