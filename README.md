# WSR Core 1.6 RELEASE

WSR Core 1.6 chuẩn hóa định dạng phiên bản x.y, nâng cấp giao diện Liquid Glass quang học cho README.html, tích hợp changelog đầy đủ giữa các phiên bản và duy trì 100% 32 Doctor gates.

Mọi phản hồi kết thúc bằng `[Context: ~X% | Trạng thái: ...]`; WSR ưu tiên usage native,
fallback estimator vẫn phải hiển thị tỷ lệ.

## Hai adapter ưu tiên

| IDE | Router native | Workflow | Skill |
|---|---|---|---|
| Codex | `~/.codex/AGENTS.md` | index trong router, JIT từ package | `~/.agents/skills` |
| Antigravity | `~/.gemini/GEMINI.md` | `~/.gemini/config/global_workflows` | `~/.gemini/antigravity/skills` |

Codex và Antigravity dùng chung kernel, nhưng binding theo discovery native riêng. Gemini là compatibility adapter của cùng `gemini-family`; Claude và Cursor bị tắt.

## Layer

- `startup`: kernel + command index, tối đa 1.000 token.
- `command`: thêm một workflow.
- `task`: thêm đúng skill đã chọn.
- `resume`: thêm session descriptor và reference trong workspace, tối đa 4.000 token.
- `diagnostic`: toàn inventory, chỉ khi yêu cầu rõ.

Ngưỡng cảnh báo: 60%; handoff: 75%; critical: 85%.
Trước `/pl`, `/ho`, `/goal` hoặc task lớn, WSR ước lượng usage dự kiến để cảnh báo sớm.

## Kiểm định và đồng bộ

`wsr_audit.py` là audit read-only sáu nhóm: integrity, structure, minimality,
dependency, resource và IDE. Quick audit chỉ đọc thay đổi; deep audit đọc toàn tree.
JSON report dùng schema `schemas/wsr-audit-report-v1.schema.json`.

```text
python scripts/wsr_audit.py --mode quick
python scripts/wsr_audit.py --mode deep --json
python tests/audit/run_fixtures.py
```

```text
python scripts/wsr_doctor.py --source-mode --strict
python scripts/wsr_audit.py --mode deep
python scripts/sync_config.py --adapter codex --target-root <sandbox> --root-override skills=<sandbox-skills>
python scripts/sync_config.py --adapter antigravity --target-root <sandbox>
```

Apply RELEASE cần `--apply` và approval token đúng build. Không có force-sync.
