---
description: Verify a released WSR source and emit a read-only reload receipt
---

# /reload

Chạy `scripts/wsr_reload.py` ở chế độ read-only theo nguồn chuẩn `https://github.com/ThayDuke/WSRCore`. Chọn đúng profile: `startup`, `command`, `task`, `resume` hoặc `diagnostic`. Dùng `--check-remote` để kiểm tra ref `origin/main` hiện có, không fetch. Dùng `--fetch-remote` chỉ khi cung cấp `--approval-token` đúng build ID. `resume` bắt buộc session file và workspace root; không khôi phục quyền cũ. Nếu router đổi, trả `RESTART_REQUIRED`.
