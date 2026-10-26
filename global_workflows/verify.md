---
description: Verify claims with fresh commands and evidence before declaring completion
---

# /verify

Verify the current task, fix, build, or release claim.

## State

- Remain read-only for source files.
- Load capability `wsr-verify` with profile `task`.
- Run the complete relevant checks freshly.
- Do not fix discovered failures without separate approval.

## Result

- Map each claim to its proving evidence.
- Report passed, failed, skipped, and unverified criteria.
- Declare completion only when every required criterion is proven.

