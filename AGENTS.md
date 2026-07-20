# WSR Core 1.0.6 — Agent Loader Contract

> [!IMPORTANT]
> Đây là nguồn WSR Core chính thức ở trạng thái `Released`.
> Cursor và Claude nằm ngoài phạm vi hỗ trợ của bản phát hành này.

- Router được `sync_config.py` render từ `bootstrap/router.md.template`.
- Router chứa source root tuyệt đối, build ID và manifest SHA-256.
- Không dò `GEMINI.md`, workflow hoặc skill bằng đường dẫn tương đối từ CWD.
- Trước mọi tác vụ, nạp toàn bộ `GEMINI.md` từ active source root.
- Với slash command, nạp đúng workflow được khai báo trong `WSR_CONTEXT.json`.
- Với task capability, nạp đúng skill và references có `capabilityId` được chọn.
- Chỉ profile `diagnostic` được phép nạp toàn bộ inventory.
- Marker runtime phải validate theo `schemas/wsr-active-v1.schema.json`.
- Codex, Gemini và Antigravity dùng native roots riêng.
- Generic chỉ được triển khai trong workspace với `--target-root` tường minh.

Các lệnh quản trị chuẩn: `/audit`, `/backup`, `/br`, `/clean`, `/commit`,
`/pl`, `/reload`, `/sync`, `/wsr` và `/ho`.
