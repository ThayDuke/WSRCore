# WSR Core 1.0.7-RELEASE

WSR Core là bộ policy, workflow, skill và công cụ kiểm soát dành cho nhiều
IDE agent. Codex, Gemini và Antigravity có adapter native; generic adapter
là lựa chọn workspace-scoped cho IDE agent khác.

## Cách nạp

Mỗi adapter khai báo logical roots tương đối dưới một target root đã xác minh.
`sync_config.py` render router chứa active source root tuyệt đối, build ID và
manifest hash. Agent vì vậy không cần dò release folder hoặc suy đoán từ CWD.

| Adapter | Target mặc định | Phạm vi |
|---|---|---|
| Codex | `CODEX_HOME`, sau đó `~/.codex` | Native |
| Gemini | `GEMINI_HOME`, sau đó `~/.gemini` | Native |
| Antigravity | `GEMINI_HOME`, sau đó `~/.gemini` | Native, dữ liệu dưới `config/` |
| Generic | Chỉ `--target-root` hoặc `WSR_WORKSPACE_ROOT` | Workspace |
| Cursor | Disabled, unsupported | Ngoài phạm vi 1.0.7 |
| Claude | Unsupported | Không triển khai |

## Quy trình an toàn

1. Chạy source Doctor:
   `python scripts/wsr_doctor.py --source-mode --strict`.
2. Xem dry-run:
   `python scripts/sync_config.py --adapter generic --target-root <workspace>`.
3. Apply chỉ sau phê duyệt:
   `python scripts/sync_config.py --adapter generic --target-root <workspace> --apply --approval-token WSR-CORE-1.0.7-RELEASE`.
4. Chạy runtime Doctor:
   `python scripts/wsr_doctor.py --runtime-mode --adapter generic --target-root <workspace> --strict`.
5. Reload theo profile và capability cần thiết; dùng `--confirm-loaded` chỉ sau
   khi mọi required entry thực sự đã được agent đọc.

Package giữ trạng thái `Released`. Việc apply vẫn cần approval token đúng build.
Không có thao tác release nào tự ghi vào runtime global.

## Progressive disclosure

- `startup`: policy, manifest, context và adapter.
- `command`: startup cộng đúng workflow đang chạy.
- `task`: command cộng skill có `capabilityId` được chọn và references của nó.
- `diagnostic`: toàn bộ inventory.

Doctor kiểm 32 gate, bao gồm identity, adapter v2, marker, router, token budget,
transaction evidence và cross-IDE conformance.
