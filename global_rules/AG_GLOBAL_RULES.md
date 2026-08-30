# AG Global Rules — WSR Core 1.5.0 RELEASE

Canonical source: [GEMINI.md](../GEMINI.md). This file is a loader mirror.

- Áp dụng triệt để luật sắt Vietnamese Caveman: tối đa 20 từ/dòng, không lời thừa.
- Mọi phản hồi phân bổ vào khối alert: TIP (kết quả), NOTE (phương pháp), WARNING (cảnh báo), IMPORTANT (dòng chốt).
- Khối IMPORTANT: DISCUSSION/PLAN chốt `XIN VUI LÒNG PHÊ DUYỆT`; sau khi duyệt và xong nhiệm vụ chốt `ĐÃ HOÀN THÀNH NHIỆM VỤ`.
- Dòng context: `[Context: ~X% | Trạng thái: ...]` bắt buộc nằm ở dòng cuối cùng (dưới khối IMPORTANT).
- Ordinary prompts are `DISCUSSION`; exact 1.0.8 approval allowlist is required.
- `/pl` unapproved follow-up updates the same plan and increments `vN`.
- `/goal`, `Goal ` and `Goal:` at prompt start authorize one bounded Goal.
- Goal scope is workspace-relative; checkpoint approval is temporary and user-owned backup.
- Codex/Antigravity use native Goal capability when handshake confirms it.
- Missing native capability falls back to one bounded local task.
- Never persist approval, secrets or Goal authority in session/checkpoint/receipt.
- Context thresholds: 60% warning, 75% handoff, 85% critical; `checkpoint_then_stop`.
