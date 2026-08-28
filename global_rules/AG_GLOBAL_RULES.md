# AG Global Rules — WSR Core 1.5.0 REVIEW

Canonical source: [GEMINI.md](../GEMINI.md). This file is a loader mirror.

- Ordinary prompts are `DISCUSSION`; exact 1.0.8 approval allowlist is required.
- `/pl` unapproved follow-up updates the same plan and increments `vN`.
- `/goal`, `Goal ` and `Goal:` at prompt start authorize one bounded Goal.
- Goal scope is workspace-relative; checkpoint approval is temporary and user-owned backup.
- Codex/Antigravity use native Goal capability when handshake confirms it.
- Missing native capability falls back to one bounded local task.
- Never persist approval, secrets or Goal authority in session/checkpoint/receipt.
- Context thresholds: 60% warning, 75% handoff, 85% critical; `checkpoint_then_stop`.
- RELEASE 1.0.8 and runtime configuration remain unchanged.
