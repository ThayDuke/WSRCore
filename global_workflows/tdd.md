---
description: Run an approval-gated red-green-refactor implementation cycle
---

# /tdd

Implement one bounded behavior through test-driven development.

## State

- Start in `DISCUSSION`.
- Load capability `wsr-tdd` with profile `task`.
- Before approval, define behavior, test target, and verification commands only.
- Exact WSR approval authorizes only the presented bounded change.

## Execution

- Create the smallest failing test and confirm expected RED.
- Implement the minimum change and confirm GREEN.
- Run relevant regression checks.
- Refactor only inside approved scope.
- Apply `wsr-verify` before completion claims.

